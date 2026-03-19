"""Subscribes to the *matches-calculated* topic.  When the Job Discovery
Service finishes matching, it publishes results here.  This subscriber
persists them into the user_matches table and clears the needs_refresh flag.
"""

import asyncio
import json
import logging
from datetime import datetime

from google.cloud import pubsub_v1
from sqlalchemy import select, update

from ..config import settings
from ..database import async_session
from ..models import User, UserMatch
from ..schemas import MatchResult

logger = logging.getLogger(__name__)

_subscriber: pubsub_v1.SubscriberClient | None = None
_main_loop: asyncio.AbstractEventLoop | None = None


def _get_subscriber() -> pubsub_v1.SubscriberClient:
    global _subscriber
    if _subscriber is None:
        _subscriber = pubsub_v1.SubscriberClient()
    return _subscriber


async def _save_match(data: dict) -> None:
    result = MatchResult(**data)

    async with async_session() as db:
        # Verify the user exists before saving
        user = await db.execute(select(User.id).where(User.id == result.user_id))
        if user.scalar_one_or_none() is None:
            logger.warning("Received matches for unknown user %s", result.user_id)
            return

        db.add(
            UserMatch(
                user_id=result.user_id,
                matched_job_ids=result.matched_job_ids,
                calculated_at=result.timestamp,
            )
        )

        await db.execute(
            update(User)
            .where(User.id == result.user_id)
            .values(needs_refresh=False)
        )

        await db.commit()

    logger.info(
        "Saved %d matches for user %s",
        len(result.matched_job_ids),
        result.user_id,
    )


def _on_message(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        data = json.loads(message.data.decode("utf-8"))
        future = asyncio.run_coroutine_threadsafe(_save_match(data), _main_loop)
        future.result()
        message.ack()
    except Exception:
        logger.exception("Failed to process matches-calculated message")
        message.nack()


async def start_subscriber() -> pubsub_v1.subscriber.futures.StreamingPullFuture | None:
    """Start the Pub/Sub pull subscriber for matches-calculated."""
    global _main_loop
    _main_loop = asyncio.get_running_loop()

    if not settings.gcp_project_id:
        logger.warning("GCP_PROJECT_ID not set — Pub/Sub subscriber disabled")
        return None

    sub_path = _get_subscriber().subscription_path(
        settings.gcp_project_id, settings.pubsub_subscription_matches
    )
    future = _get_subscriber().subscribe(sub_path, callback=_on_message)
    logger.info("Pub/Sub subscriber listening on %s", sub_path)
    return future
