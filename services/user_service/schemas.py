from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------
class UserOut(BaseModel):
    id: str
    email: str | None = None
    display_name: str | None = None
    bio: str | None = None
    skills: list[str] = []
    location: str | None = None
    remote_preference: bool = True
    salary_min: int | None = None
    salary_max: int | None = None
    needs_refresh: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """PATCH /me request body — all fields optional."""
    email: str | None = None
    display_name: str | None = None
    bio: str | None = None
    skills: list[str] | None = None
    location: str | None = None
    remote_preference: bool | None = None
    salary_min: int | None = None
    salary_max: int | None = None


# ---------------------------------------------------------------------------
# Match history
# ---------------------------------------------------------------------------
class MatchOut(BaseModel):
    matched_job_ids: list[int]
    calculated_at: datetime

    model_config = {"from_attributes": True}


class MatchesResponse(BaseModel):
    matches: list[MatchOut]
    total: int


# ---------------------------------------------------------------------------
# Pub/Sub contract (mirrors job_discovery_service schemas)
# ---------------------------------------------------------------------------
class RefreshFilters(BaseModel):
    location: str | None = None
    remote: bool | None = None
    salary_min: int | None = None
    salary_max: int | None = None


class RefreshRequest(BaseModel):
    """Published to user-refresh-requested topic."""
    user_id: str
    user_vector: list[float]
    filters: RefreshFilters = RefreshFilters()


class MatchResult(BaseModel):
    """Received from matches-calculated subscription."""
    user_id: str
    matched_job_ids: list[int]
    timestamp: datetime
