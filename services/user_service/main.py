"""FastAPI entry-point for the User Service.

Startup:
    uvicorn user_service.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.ws import router as ws_router
from .database import init_db
from .messaging.subscriber import start_subscriber

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    streaming_pull = await start_subscriber()
    logger.info("User Service is live")
    yield
    if streaming_pull is not None:
        streaming_pull.cancel()
    logger.info("User Service shutting down")


app = FastAPI(
    title="User Service",
    description="Profile management, event dispatch, and match history",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

app.include_router(router)
app.include_router(ws_router)
