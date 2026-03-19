"""Publishes a *user-refresh-requested* message to Pub/Sub so the Job
Discovery Service can run a new vector match for this user.
"""

import logging

from google.cloud import pubsub_v1

from ..config import settings
from ..schemas import RefreshFilters, RefreshRequest

logger = logging.getLogger(__name__)

_publisher: pubsub_v1.PublisherClient | None = None


def _get_publisher() -> pubsub_v1.PublisherClient:
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


async def publish_refresh_request(
    user_id: str,
    user_vector: list[float],
    filters: RefreshFilters,
) -> None:
    if not settings.gcp_project_id:
        logger.warning("GCP_PROJECT_ID not set — skipping Pub/Sub publish")
        return

    topic = _get_publisher().topic_path(
        settings.gcp_project_id, settings.pubsub_topic_refresh
    )

    message = RefreshRequest(
        user_id=user_id,
        user_vector=user_vector,
        filters=filters,
    )

    _get_publisher().publish(
        topic, data=message.model_dump_json().encode("utf-8")
    ).result()

    logger.info("Published refresh request for user %s", user_id)
