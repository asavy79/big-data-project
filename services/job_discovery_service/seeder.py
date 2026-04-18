"""Auto-seed the jobs table on startup when the database is empty.

Re-uses the same JSearch API fetching logic as the cron_fetcher script,
but runs as part of the FastAPI lifespan so no manual step is needed.
"""

import asyncio
import logging
from datetime import datetime

import httpx
from sqlalchemy import func, select

from .config import settings
from .database import async_session
from .messaging.publisher import publish_jobs_ingested
from .models import Job
from .worker.embedder import generate_embeddings_batch

logger = logging.getLogger(__name__)

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_PAGE_RETRIES = 3
def _build_location(job: dict) -> str | None:
    city = job.get("job_city")
    state = job.get("job_state")
    country = job.get("job_country")
    parts = [p for p in (city, state, country) if p]
    return ", ".join(parts) if parts else None


def _build_embedding_text(job: dict) -> str:
    sections = [job.get("job_title", ""), job.get("job_description", "")]
    highlights = job.get("job_highlights") or {}
    for key in ("Qualifications", "Responsibilities"):
        items = highlights.get(key, [])
        if items:
            sections.append(f"{key}: " + "; ".join(items))
    return "\n".join(s for s in sections if s)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _normalize(raw: dict) -> dict:
    return {
        "external_id": raw.get("job_id", ""),
        "title": raw.get("job_title", "Untitled"),
        "company": raw.get("employer_name", "Unknown"),
        "description": raw.get("job_description"),
        "location": _build_location(raw),
        "remote": raw.get("job_is_remote"),
        "salary_min": raw.get("job_min_salary"),
        "salary_max": raw.get("job_max_salary"),
        "url": raw.get("job_apply_link"),
        "posted_at": _parse_datetime(raw.get("job_posted_at_datetime_utc")),
        "source": "jsearch",
        "embedding_text": _build_embedding_text(raw),
    }


def _jsearch_timeout() -> httpx.Timeout:
    t = float(settings.jsearch_http_timeout_seconds)
    return httpx.Timeout(t, connect=min(30.0, t))


async def _fetch_jsearch_page(
    client: httpx.AsyncClient,
    page: int,
    headers: dict[str, str],
) -> list[dict]:
    params = {
        "query": settings.jsearch_query,
        "date_posted": settings.jsearch_date_posted,
        "num_pages": 1,
        "page": page,
    }
    last_err: BaseException | None = None
    for attempt in range(1, JSEARCH_PAGE_RETRIES + 1):
        try:
            resp = await client.get(
                JSEARCH_URL,
                headers=headers,
                params=params,
                timeout=_jsearch_timeout(),
            )
            resp.raise_for_status()
            page_jobs = resp.json().get("data", []) or []
            logger.info("Seed fetch page %d: %d jobs", page, len(page_jobs))
            return page_jobs
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
            last_err = e
            logger.warning(
                "JSearch page %d attempt %d/%d failed (%s), retrying…",
                page,
                attempt,
                JSEARCH_PAGE_RETRIES,
                type(e).__name__,
            )
            if attempt < JSEARCH_PAGE_RETRIES:
                await asyncio.sleep(2**attempt)
    assert last_err is not None
    raise last_err


async def _fetch_from_jsearch() -> list[dict]:
    if not settings.rapidapi_key:
        logger.warning("RAPIDAPI_KEY not set — cannot seed jobs from JSearch")
        return []

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": settings.jsearch_host,
    }

    num_pages = settings.jsearch_num_pages
    all_jobs: list[dict] = []

    # Sequential pages avoid hammering RapidAPI with dozens of parallel requests
    # (which often causes ReadTimeout). Stop early when a page returns no results.
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(limits=limits) as client:
        for page in range(1, num_pages + 1):
            page_jobs = await _fetch_jsearch_page(client, page, headers)
            all_jobs.extend(page_jobs)
            if not page_jobs:
                logger.info(
                    "Stopping after empty page %d (no more JSearch results for this query)",
                    page,
                )
                break

    return all_jobs


async def _ingest_normalized_seed_jobs(normalized: list[dict]) -> int:
    """Insert jobs; skip rows whose external_id already exists (same as cron_fetcher)."""
    if not normalized:
        return 0
    texts = [j["embedding_text"] for j in normalized]
    embeddings = await generate_embeddings_batch(texts)

    ingested = 0
    async with async_session() as db:
        for job, emb in zip(normalized, embeddings):
            exists = await db.execute(
                select(Job.id).where(Job.external_id == job["external_id"])
            )
            if exists.scalar_one_or_none() is not None:
                continue
            logger.debug(
                "Seeding job: %s (%s - %s)",
                job["title"],
                job["salary_min"],
                job["salary_max"],
            )
            db.add(
                Job(
                    external_id=job["external_id"],
                    title=job["title"],
                    company=job["company"],
                    description=job["description"],
                    location=job["location"],
                    remote=job["remote"],
                    salary_min=job["salary_min"],
                    salary_max=job["salary_max"],
                    url=job["url"],
                    posted_at=job["posted_at"],
                    source=job["source"],
                    embedding=emb,
                )
            )
            ingested += 1
        await db.commit()
    return ingested


async def seed_jobs(*, force: bool = False) -> int:
    """Fetch from JSearch and insert new jobs (skips duplicate external_id).

    If ``force`` is False, only runs when the jobs table is empty (startup behavior).
    If ``force`` is True, always fetches; existing job_ids are not duplicated.

    Returns the number of newly inserted rows.
    """
    if not force:
        async with async_session() as db:
            count = (await db.execute(select(func.count(Job.id)))).scalar_one()
        if count > 0:
            logger.info("Jobs table already has %d rows — skipping seed", count)
            return 0
        logger.info("Jobs table is empty — seeding from JSearch API …")
    else:
        logger.info(
            "Force seed: fetching from JSearch (query=%r, date_posted=%s, pages=1..%d) …",
            settings.jsearch_query,
            settings.jsearch_date_posted,
            settings.jsearch_num_pages,
        )

    raw_jobs = await _fetch_from_jsearch()
    if not raw_jobs:
        logger.warning("No jobs returned from JSearch")
        return 0

    normalized = [_normalize(j) for j in raw_jobs]
    ingested = await _ingest_normalized_seed_jobs(normalized)
    logger.info("Inserted %d new jobs (skipped duplicates already in DB)", ingested)

    if ingested > 0:
        await publish_jobs_ingested(ingested)
    return ingested


async def seed_jobs_if_empty() -> None:
    """Check whether the jobs table has rows; if not, fetch and ingest."""
    await seed_jobs(force=False)
