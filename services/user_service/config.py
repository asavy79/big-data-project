from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobdb"

    # GCP
    gcp_project_id: str = ""
    pubsub_topic_refresh: str = "user-refresh-requested"
    pubsub_subscription_matches: str = "matches-calculated-sub"

    # Vertex AI / LangChain embeddings
    vertex_ai_location: str = "us-central1"
    embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
