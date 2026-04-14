from pydantic import Field
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
    jsearch_query: str = "software engineer in United States"
    jsearch_date_posted: str = "3days"
    jsearch_num_pages: int = 1

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
