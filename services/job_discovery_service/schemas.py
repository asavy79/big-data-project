from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared filter object used by both the REST API and Pub/Sub messages
# ---------------------------------------------------------------------------
class SearchFilters(BaseModel):
    location: str | None = None
    remote: bool | None = None
    salary_min: int | None = None
    salary_max: int | None = None


# ---------------------------------------------------------------------------
# REST — GET /jobs/{id}
# ---------------------------------------------------------------------------
class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    remote: bool = False
    salary_min: int | None = None
    salary_max: int | None = None
    url: str | None = None
    source: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# REST — POST /jobs/search
# ---------------------------------------------------------------------------
class JobSearchRequest(BaseModel):
    user_vector: list[float] | None = None
    query: str | None = None
    filters: SearchFilters = SearchFilters()
    limit: int = 10


class JobSearchResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# ---------------------------------------------------------------------------
# REST — POST /internal/ingest
# ---------------------------------------------------------------------------
class JobIngestItem(BaseModel):
    external_id: str
    title: str
    company: str
    description: str
    location: str | None = None
    remote: bool = False
    salary_min: int | None = None
    salary_max: int | None = None
    url: str | None = None
    source: str | None = None


class JobIngestRequest(BaseModel):
    jobs: list[JobIngestItem]


class IngestResult(BaseModel):
    ingested: int
    total_submitted: int


# ---------------------------------------------------------------------------
# Pub/Sub — user-refresh-requested  (incoming message)
# ---------------------------------------------------------------------------
class MatchRequest(BaseModel):
    user_id: str
    user_vector: list[float]
    filters: SearchFilters = SearchFilters()


# ---------------------------------------------------------------------------
# Pub/Sub — matches-calculated  (outgoing message)
# ---------------------------------------------------------------------------
class MatchResult(BaseModel):
    user_id: str
    matched_job_ids: list[int]
    timestamp: datetime
