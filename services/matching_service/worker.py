"""Pub/Sub workers: subscribes to *user-refresh-requested* and *jobs-ingested*,
coordinates matching by calling the Job and User service APIs, and publishes
results to *matches-calculated*.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import httpx
from google.cloud import pubsub_v1

from .config import settings
from .schemas import ActiveUser, MatchRequest, MatchResult

logger = logging.getLogger(__name__)

_publisher: pubsub_v1.PublisherClient | None = None
_subscriber: pubsub_v1.SubscriberClient | None = None
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


def _publish_match_result(user_id: str, matched_job_ids: list[int]) -> None:
    topic = _get_publisher().topic_path(
        settings.gcp_project_id, settings.pubsub_topic_matches
    )
    payload = MatchResult(
        user_id=user_id,
        matched_job_ids=matched_job_ids,
        timestamp=datetime.now(timezone.utc),
    )
    _get_publisher().publish(
        topic, data=payload.model_dump_json().encode("utf-8")
    ).result()
    logger.info("Published matches for user %s → %s", user_id, matched_job_ids)


async def _search_jobs(user_vector: list[float], filters: dict, limit: int) -> list[int]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.job_service_url}/jobs/search",
            json={
                "user_vector": user_vector,
                "filters": filters,
                "limit": limit,
            },
            timeout=30,
        )
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
        return [j["id"] for j in jobs]


# ------------------------------------------------------------------
# Handler: single user refresh (profile save)
# ------------------------------------------------------------------
async def handle_user_refresh(data: dict) -> None:
    request = MatchRequest(**data)
    matched_ids = await _search_jobs(
        request.user_vector,
        request.filters.model_dump(exclude_none=True),
        settings.match_limit,
    )
    _publish_match_result(request.user_id, matched_ids)


# ------------------------------------------------------------------
# Handler: new jobs ingested → re-match all active users
# ------------------------------------------------------------------
async def handle_jobs_ingested(data: dict) -> None:
    count = data.get("count", 0)
    logger.info("Jobs-ingested event received (count=%d), re-matching all active users", count)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.user_service_url}/internal/active-users",
            headers={"X-Internal-Key": settings.internal_api_key},
            timeout=30,
        )
        resp.raise_for_status()
        users_data = resp.json()

    users = [ActiveUser(**u) for u in users_data]
    logger.info("Fetched %d active users for re-matching", len(users))

    for user in users:
        try:
            matched_ids = await _search_jobs(
                user.user_vector,
                user.filters.model_dump(exclude_none=True),
                settings.match_limit,
            )
            _publish_match_result(user.user_id, matched_ids)
        except Exception:
            logger.exception("Failed to re-match user %s", user.user_id)


# ------------------------------------------------------------------
# Pub/Sub callbacks (run in gRPC thread, dispatch to main loop)
# ------------------------------------------------------------------
def _on_refresh_message(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        data = json.loads(message.data.decode("utf-8"))
        future = asyncio.run_coroutine_threadsafe(handle_user_refresh(data), _main_loop)
        future.result()
        message.ack()
    except Exception:
        logger.exception("Failed to process user-refresh-requested message")
        message.nack()


def _on_ingested_message(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        data = json.loads(message.data.decode("utf-8"))
        future = asyncio.run_coroutine_threadsafe(handle_jobs_ingested(data), _main_loop)
        future.result()
        message.ack()
    except Exception:
        logger.exception("Failed to process jobs-ingested message")
        message.nack()


# ------------------------------------------------------------------
# Lifecycle
# ------------------------------------------------------------------
async def start_subscribers() -> list[pubsub_v1.subscriber.futures.StreamingPullFuture]:
    global _main_loop
    _main_loop = asyncio.get_running_loop()

    if not settings.gcp_project_id:
        logger.warning("GCP_PROJECT_ID not set — Pub/Sub subscribers disabled")
        return []

    sub = _get_subscriber()
    futures = []

    refresh_path = sub.subscription_path(
        settings.gcp_project_id, settings.pubsub_sub_refresh
    )
    f1 = sub.subscribe(refresh_path, callback=_on_refresh_message)
    logger.info("Listening on %s", refresh_path)
    futures.append(f1)

    ingested_path = sub.subscription_path(
        settings.gcp_project_id, settings.pubsub_sub_ingested
    )
    f2 = sub.subscribe(ingested_path, callback=_on_ingested_message)
    logger.info("Listening on %s", ingested_path)
    futures.append(f2)

    return futures
