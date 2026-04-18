from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required — set DATABASE_URL in env (never defaults to localhost in production).
    database_url: str = Field(
        ...,
        description="Async SQLAlchemy URL; set env DATABASE_URL",
    )
    gcp_project_id: str = ""
    pubsub_topic_ingested: str = "jobs-ingested"
    vertex_ai_location: str = "us-central1"
    embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768
    # Vertex text-embedding-004 caps input at ~20k tokens per request; LangChain
    # batches multiple strings into one RPC, so we truncate and embed one doc per call.
    max_embedding_input_chars: int = 12000
    embedding_request_concurrency: int = 5
    internal_api_key: str = "changeme"

    # JSearch (RapidAPI)
    rapidapi_key: str = ""
    jsearch_host: str = "jsearch.p.rapidapi.com"
    # JSearch: ~10 results per page; page and num_pages each allow up to 50 (RapidAPI pricing tiers apply).
    # date_posted: all | today | 3days | week | month — "month" ≈ jobs from the last month.
    jsearch_query: str = (
        "data science OR machine learning engineer OR ML engineer in United States"
    )
    jsearch_date_posted: str = "month"
    jsearch_num_pages: int = 30
    # JSearch can be slow under load; parallel bursts often hit ReadTimeout at 30s.
    jsearch_http_timeout_seconds: float = 120.0

    @field_validator("jsearch_num_pages")
    @classmethod
    def _clamp_pages(cls, v: int) -> int:
        # JSearch allows page 1–50; each page is up to ~10 jobs.
        return max(1, min(int(v), 50))

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
