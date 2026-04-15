"""Pub/Sub workers: subscribes to *user-refresh-requested* and *jobs-ingested*,
coordinates matching by calling the Job and User service APIs, and publishes
results to *matches-calculated*.

In production (Cloud Run), use push subscriptions to HTTP routes in ``pubsub_routes``
and set ``PUBSUB_USE_PULL_SUBSCRIBER=false`` so nothing holds a streaming pull.
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone

import httpx
from google.cloud import pubsub_v1

from .config import settings
from .schemas import ActiveUser, MatchRequest, MatchResult

logger = logging.getLogger(__name__)


def _outbound_auth_headers(audience_base: str) -> dict[str, str]:
    """Bearer token for Cloud Run service-to-service (target audience = service root URL)."""
    base = (audience_base or "").strip().rstrip("/")
    if not base:
        return {}
    low = base.lower()
    if "localhost" in low or "127.0.0.1" in low:
        return {}
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        token = google.oauth2.id_token.fetch_id_token(
            google.auth.transport.requests.Request(),
            base,
        )
        return {"Authorization": f"Bearer {token}"}
    except Exception as exc:
        logger.warning(
            "Could not get identity token for %s (%s); outbound call may get 403 on Cloud Run",
            base,
            exc,
        )
        return {}


def decode_pubsub_push_message_data(body: dict) -> dict:
    """Parse a Pub/Sub push JSON body and return the decoded application payload."""
    msg = body.get("message") or {}
    raw_b64 = msg.get("data") or ""
    decoded = base64.b64decode(raw_b64).decode("utf-8")
    return json.loads(decoded)

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
    if not settings.gcp_project_id:
        raise RuntimeError(
            "GCP_PROJECT_ID (or GOOGLE_CLOUD_PROJECT on Cloud Run) must be set to publish to Pub/Sub"
        )
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
    base = settings.job_service_url.rstrip("/")
    url = f"{base}/jobs/search"
    headers = _outbound_auth_headers(base)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "user_vector": user_vector,
                    "filters": filters,
                    "limit": limit,
                },
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            jobs = resp.json().get("jobs", [])
            return [j["id"] for j in jobs]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logger.error(
                "403 from %s — target Cloud Run requires auth: grant *this* service's runtime "
                "service account the role roles/run.invoker on job-discovery-service.",
                url,
            )
        raise
    except httpx.ConnectError as e:
        logger.error(
            "Cannot reach job discovery at %s (check JOB_SERVICE_URL): %s",
            url,
            e,
        )
        raise


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

    ubase = settings.user_service_url.rstrip("/")
    users_url = f"{ubase}/internal/active-users"
    headers = {
        **_outbound_auth_headers(ubase),
        "X-Internal-Key": settings.internal_api_key,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(users_url, headers=headers, timeout=30)
            resp.raise_for_status()
            users_data = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logger.error(
                "403 from %s — grant this service account roles/run.invoker on user-service.",
                users_url,
            )
        raise
    except httpx.ConnectError as e:
        logger.error("Cannot reach user service at %s: %s", users_url, e)
        raise

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

    if not settings.pubsub_use_pull_subscriber:
        logger.info("Pub/Sub streaming pull disabled — using push HTTP endpoints")
        return []

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
