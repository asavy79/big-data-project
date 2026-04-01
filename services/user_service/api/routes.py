from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..embedder import generate_profile_embedding
from ..messaging.publisher import publish_refresh_request
from ..models import User, UserMatch
from ..schemas import (
    ActiveUserOut,
    MatchesResponse,
    MatchOut,
    RefreshFilters,
    UserOut,
    UserUpdate,
)
from .auth import get_current_uid, get_db, verify_internal

router = APIRouter()


# ------------------------------------------------------------------
# GET /me  — retrieve profile (lazy-create if first visit)
# ------------------------------------------------------------------
@router.get("/me", response_model=UserOut)
async def get_me(
    uid: str = Depends(get_current_uid),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_or_create_user(db, uid)
    return user


# ------------------------------------------------------------------
# PATCH /me  — update profile → regenerate embedding → fire Pub/Sub
# ------------------------------------------------------------------
@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    uid: str = Depends(get_current_uid),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_or_create_user(db, uid)

    changed = False
    for field, value in body.model_dump(exclude_unset=True).items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed = True

    if changed:
        user.embedding = await generate_profile_embedding(user)
        user.needs_refresh = True
        await db.commit()
        await db.refresh(user)

        await publish_refresh_request(
            user_id=user.id,
            user_vector=list(user.embedding),
            filters=RefreshFilters(
                location=user.location,
                remote=user.remote_preference,
                salary_min=user.salary_min,
                salary_max=user.salary_max,
                skills=user.skills or None,
            ),
        )

    return user


# ------------------------------------------------------------------
# GET /me/matches  — latest match sets from the Job Discovery Service
# ------------------------------------------------------------------
@router.get("/me/matches", response_model=MatchesResponse)
async def get_matches(
    uid: str = Depends(get_current_uid),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserMatch)
        .where(UserMatch.user_id == uid)
        .order_by(UserMatch.calculated_at.desc())
        .limit(10)
    )
    rows = result.scalars().all()

    return MatchesResponse(
        matches=[MatchOut.model_validate(r) for r in rows],
        total=len(rows),
    )


# ------------------------------------------------------------------
# GET /internal/active-users  — all users with embeddings (service-to-service)
# ------------------------------------------------------------------
@router.get(
    "/internal/active-users",
    response_model=list[ActiveUserOut],
    dependencies=[Depends(verify_internal)],
)
async def get_active_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.embedding.is_not(None))
    )
    users = result.scalars().all()
    return [
        ActiveUserOut(
            user_id=u.id,
            user_vector=list(u.embedding),
            filters=RefreshFilters(
                location=u.location,
                remote=u.remote_preference,
                salary_min=u.salary_min,
                salary_max=u.salary_max,
                skills=u.skills,
            ),
        )
        for u in users
    ]


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------
@router.get("/health")
async def health():
    return {"status": "ok", "service": "user"}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
async def _get_or_create_user(db: AsyncSession, uid: str) -> User:
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=uid)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
