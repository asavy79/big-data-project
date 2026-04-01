from datetime import datetime

from pydantic import BaseModel


class SearchFilters(BaseModel):
    location: str | None = None
    remote: bool | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    skills: list[str] | None = None


class MatchRequest(BaseModel):
    """Incoming Pub/Sub message from user-refresh-requested."""
    user_id: str
    user_vector: list[float]
    filters: SearchFilters = SearchFilters()


class MatchResult(BaseModel):
    """Outgoing Pub/Sub message to matches-calculated."""
    user_id: str
    matched_job_ids: list[int]
    timestamp: datetime


class ActiveUser(BaseModel):
    """Shape returned by the User Service internal endpoint."""
    user_id: str
    user_vector: list[float]
    filters: SearchFilters = SearchFilters()
