"""Publishes a *jobs-ingested* signal to Pub/Sub so the Matching Service
can re-run matching for all active users against the new jobs.
"""

import json
import logging

from google.cloud import pubsub_v1

from ..config import settings

logger = logging.getLogger(__name__)

_publisher: pubsub_v1.PublisherClient | None = None


def _get_publisher() -> pubsub_v1.PublisherClient:
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


async def publish_jobs_ingested(count: int) -> None:
    if not settings.gcp_project_id:
        logger.warning("GCP_PROJECT_ID not set — skipping Pub/Sub publish")
        return

    topic = _get_publisher().topic_path(
        settings.gcp_project_id, settings.pubsub_topic_ingested
    )

    payload = json.dumps({"count": count}).encode("utf-8")
    _get_publisher().publish(topic, data=payload).result()

    logger.info("Published jobs-ingested event (count=%d)", count)
