"""FastAPI entry-point for the Matching Service.

Startup:
    uvicorn matching_service.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .worker import start_subscribers

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    futures = await start_subscribers()
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "matching"}
