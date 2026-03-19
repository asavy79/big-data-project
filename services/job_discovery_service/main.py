"""FastAPI entry-point for the Job Discovery Service.

Startup:
    uvicorn job_discovery_service.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.router import router
from .database import init_db
from .seeder import seed_jobs_if_empty
from .worker.processor import start_subscriber

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_jobs_if_empty()
    streaming_pull = await start_subscriber()
    logger.info("Job Discovery Service is live")
    yield
    if streaming_pull is not None:
        streaming_pull.cancel()
    logger.info("Job Discovery Service shutting down")


app = FastAPI(
    title="Job Discovery Service",
    description="Hybrid vector search & matching engine for job listings",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
