from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str = ""

    # Pub/Sub
    pubsub_sub_refresh: str = "user-refresh-requested-sub"
    pubsub_sub_ingested: str = "jobs-ingested-sub"
    pubsub_topic_matches: str = "matches-calculated"

    # Downstream services
    job_service_url: str = "http://localhost:8001"
    user_service_url: str = "http://localhost:8002"
    internal_api_key: str = "changeme"

    match_limit: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
