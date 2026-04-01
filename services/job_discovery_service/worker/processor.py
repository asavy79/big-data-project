"""Pub/Sub worker: subscribes to *user-refresh-requested*, runs the pgvector
similarity search, and publishes the result to *matches-calculated*.

The subscriber callback executes in a thread-pool managed by the google-cloud
client.  Each callback spins up its own asyncio event loop so it can reuse the
async SQLAlchemy session without blocking the main FastAPI loop.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from google.cloud import pubsub_v1
from sqlalchemy import or_, select

from ..config import settings
from ..database import async_session
from ..models import Job
from ..schemas import MatchRequest, MatchResult

logger = logging.getLogger(__name__)

_publisher: pubsub_v1.PublisherClient | None = None
_subscriber: pubsub_v1.SubscriberClient | None = None
_executor = ThreadPoolExecutor(max_workers=4)
_main_loop: asyncio.AbstractEventLoop | None = None


def _get_publisher() -> pubsub_v1.PublisherClient:
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


def _get_subscriber() -> pubsub_v1.SubscriberClient:
    global _subscriber
    if _subscriber is None:
        _subscriber = pubsub_v1.SubscriberClient()
    return _subscriber


# ------------------------------------------------------------------
# Core matching logic (async)
# ------------------------------------------------------------------
async def _run_match(data: dict) -> None:
    request = MatchRequest(**data)

    async with async_session() as db:
        query = select(Job.id).where(Job.embedding.is_not(None))

        if request.filters.location:
            query = query.where(
                Job.location.ilike(f"%{request.filters.location}%")
            )
        if request.filters.remote is not None and request.filters.remote == False:
            query = query.where(
                or_(Job.remote.is_(None), Job.remote == False)
            )
        if request.filters.salary_min is not None:
            query = query.where(
                or_(
                    Job.salary_max.is_(None),
                    Job.salary_max >= request.filters.salary_min,
                )
            )
        if request.filters.skills:
            query = query.where(
                or_(
                    Job.description.is_(None),
                    *(Job.description.ilike(f"%{skill}%") for skill in request.filters.skills),
                )
            )

        query = query.order_by(
            Job.embedding.cosine_distance(request.user_vector)
        ).limit(10)

        result = await db.execute(query)
        matched_ids = [row[0] for row in result.all()]

    payload = MatchResult(
        user_id=request.user_id,
        matched_job_ids=matched_ids,
        timestamp=datetime.now(timezone.utc),
    )

    topic = _get_publisher().topic_path(
        settings.gcp_project_id, settings.pubsub_topic_matches
    )
    _get_publisher().publish(
        topic, data=payload.model_dump_json().encode("utf-8")
    ).result()

    logger.info("Published matches for user %s → %s", request.user_id, matched_ids)


# ------------------------------------------------------------------
# Pub/Sub callback (runs in a thread managed by the gRPC subscriber)
# ------------------------------------------------------------------
def _on_message(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        data = json.loads(message.data.decode("utf-8"))
        future = asyncio.run_coroutine_threadsafe(_run_match(data), _main_loop)
        future.result()
        message.ack()
    except Exception:
        logger.exception("Failed to process Pub/Sub message")
        message.nack()


# ------------------------------------------------------------------
# Lifecycle
# ------------------------------------------------------------------
async def start_subscriber() -> pubsub_v1.subscriber.futures.StreamingPullFuture | None:
    """Start the Pub/Sub pull subscriber.  Returns the streaming future so
    the caller can cancel it on shutdown."""
    global _main_loop
    _main_loop = asyncio.get_running_loop()

    if not settings.gcp_project_id:
        logger.warning("GCP_PROJECT_ID not set — Pub/Sub subscriber disabled")
        return None

    sub_path = _get_subscriber().subscription_path(
        settings.gcp_project_id, settings.pubsub_subscription
    )
    future = _get_subscriber().subscribe(sub_path, callback=_on_message)
    logger.info("Pub/Sub subscriber listening on %s", sub_path)
    return future
