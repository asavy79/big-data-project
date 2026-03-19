"""Firebase UID header validation.

In production, swap this for full Firebase Admin SDK token verification:
    firebase_admin.auth.verify_id_token(token)

For now we trust the gateway / API-GW to forward a verified UID header.
"""

from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_uid(x_firebase_uid: str = Header(...)) -> str:
    """Extract the Firebase UID injected by the API gateway."""
    if not x_firebase_uid.strip():
        raise HTTPException(status_code=401, detail="Missing Firebase UID")
    return x_firebase_uid.strip()
