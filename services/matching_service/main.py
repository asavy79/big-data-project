"""FastAPI entry-point for the Matching Service.

Startup:
    uvicorn matching_service.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .pubsub_routes import router as pubsub_router
from .worker import start_subscribers

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "GCP project for Pub/Sub: %s",
        settings.gcp_project_id or "(missing — set GCP_PROJECT_ID or rely on GOOGLE_CLOUD_PROJECT on Cloud Run)",
    )
    logger.info(
        "Downstream URLs: JOB_SERVICE_URL=%s USER_SERVICE_URL=%s",
        settings.job_service_url,
        settings.user_service_url,
    )
    if settings.gcp_project_id and (
        "localhost" in settings.job_service_url
        or "localhost" in settings.user_service_url
    ):
        logger.warning(
            "JOB_SERVICE_URL / USER_SERVICE_URL look like local defaults; "
            "set them to your Cloud Run HTTPS URLs (e.g. https://job-discovery-service-....run.app)."
        )
    futures = await start_subscribers()
    if not settings.pubsub_use_pull_subscriber:
        logger.info(
            "Pub/Sub pull is disabled — refresh/ingest messages only arrive via *push* to "
            "POST /internal/pubsub/user-refresh and /internal/pubsub/jobs-ingested. "
            "In GCP, subscriptions must use push endpoints to this service URL (not empty pushConfig)."
        )
    logger.info("Matching Service is live")
    yield
    for f in futures:
        f.cancel()
    logger.info("Matching Service shutting down")


app = FastAPI(
    title="Matching Service",
    description="Coordinates vector-based job matching between the Job and User services",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(pubsub_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "matching"}
