from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required — set DATABASE_URL in env (never defaults to localhost in production).
    database_url: str = Field(
        ...,
        description="Async SQLAlchemy URL; set env DATABASE_URL",
    )

    # GCP
    gcp_project_id: str = ""
    pubsub_topic_refresh: str = "user-refresh-requested"
    pubsub_subscription_matches: str = "matches-calculated-sub"

    # Service-to-service auth
    internal_api_key: str = "changeme"

    # Vertex AI / LangChain embeddings
    vertex_ai_location: str = "us-central1"
    embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
