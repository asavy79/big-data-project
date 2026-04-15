"""Pub/Sub push delivery for *matches-calculated* (scale-to-zero friendly)."""

import logging

from fastapi import APIRouter, HTTPException, Request

from ..messaging.subscriber import decode_pubsub_push_message_data, process_matches_calculated

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/pubsub", tags=["internal"])


@router.post("/matches-calculated")
async def push_matches_calculated(request: Request) -> None:
    try:
        body = await request.json()
        data = decode_pubsub_push_message_data(body)
        await process_matches_calculated(data)
    except Exception:
        logger.exception("push matches-calculated failed")
        raise HTTPException(status_code=500, detail="processing failed") from None
