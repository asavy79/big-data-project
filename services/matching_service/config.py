import os

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Prefer GCP_PROJECT_ID; Cloud Run also sets GOOGLE_CLOUD_PROJECT (used as fallback below).
    gcp_project_id: str = ""

    # Pub/Sub — set PUBSUB_USE_PULL_SUBSCRIBER=false for Cloud Run (push HTTP instead).
    pubsub_use_pull_subscriber: bool = True
    pubsub_sub_refresh: str = "user-refresh-requested-sub"
    pubsub_sub_ingested: str = "jobs-ingested-sub"
    pubsub_topic_matches: str = "matches-calculated"

    # Downstream services
    job_service_url: str = "http://localhost:8001"
    user_service_url: str = "http://localhost:8002"
    internal_api_key: str = "changeme"

    match_limit: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _project_id_from_cloud_run(self) -> "Settings":
        if self.gcp_project_id:
            return self
        auto = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
        if auto:
            return self.model_copy(update={"gcp_project_id": auto})
        return self


settings = Settings()
