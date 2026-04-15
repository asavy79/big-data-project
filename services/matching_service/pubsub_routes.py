"""HTTP handlers for Pub/Sub *push* delivery (scale-to-zero friendly)."""

import logging

from fastapi import APIRouter, HTTPException, Request

from .worker import (
    decode_pubsub_push_message_data,
    handle_jobs_ingested,
    handle_user_refresh,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/pubsub", tags=["internal"])


@router.post("/user-refresh")
async def push_user_refresh(request: Request) -> None:
    try:
        body = await request.json()
        data = decode_pubsub_push_message_data(body)
        await handle_user_refresh(data)
    except Exception:
        logger.exception("push user-refresh failed")
        raise HTTPException(status_code=500, detail="processing failed") from None


@router.post("/jobs-ingested")
async def push_jobs_ingested(request: Request) -> None:
    try:
        body = await request.json()
        data = decode_pubsub_push_message_data(body)
        await handle_jobs_ingested(data)
    except Exception:
        logger.exception("push jobs-ingested failed")
        raise HTTPException(status_code=500, detail="processing failed") from None
