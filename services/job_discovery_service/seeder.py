"""Auto-seed the jobs table on startup when the database is empty.

Re-uses the same JSearch API fetching logic as the cron_fetcher script,
but runs as part of the FastAPI lifespan so no manual step is needed.
"""

import logging

import httpx
from sqlalchemy import func, select

from .config import settings
from .database import async_session
from .models import Job
from .worker.embedder import generate_embeddings_batch

logger = logging.getLogger(__name__)

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"


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


def _normalize(raw: dict) -> dict:
    return {
        "external_id": raw.get("job_id", ""),
        "title": raw.get("job_title", "Untitled"),
        "company": raw.get("employer_name", "Unknown"),
        "description": raw.get("job_description"),
        "location": _build_location(raw),
        "remote": raw.get("job_is_remote", False),
        "salary_min": raw.get("job_min_salary"),
        "salary_max": raw.get("job_max_salary"),
        "url": raw.get("job_apply_link"),
        "source": "jsearch",
        "embedding_text": _build_embedding_text(raw),
    }


async def _fetch_from_jsearch() -> list[dict]:
    if not settings.rapidapi_key:
        logger.warning("RAPIDAPI_KEY not set — cannot seed jobs from JSearch")
        return []

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": settings.jsearch_host,
    }

    all_jobs: list[dict] = []
    async with httpx.AsyncClient() as client:
        for page in range(1, settings.jsearch_num_pages + 1):
            params = {
                "query": settings.jsearch_query,
                "date_posted": settings.jsearch_date_posted,
                "num_pages": 1,
                "page": page,
            }
            resp = await client.get(
                JSEARCH_URL, headers=headers, params=params, timeout=30
            )
            resp.raise_for_status()
            page_jobs = resp.json().get("data", [])
            all_jobs.extend(page_jobs)
            logger.info("Seed fetch page %d: %d jobs", page, len(page_jobs))

    return all_jobs


async def seed_jobs_if_empty() -> None:
    """Check whether the jobs table has rows; if not, fetch and ingest."""
    async with async_session() as db:
        count = (await db.execute(select(func.count(Job.id)))).scalar_one()

    if count > 0:
        logger.info("Jobs table already has %d rows — skipping seed", count)
        return

    logger.info("Jobs table is empty — seeding from JSearch API …")
    raw_jobs = await _fetch_from_jsearch()
    if not raw_jobs:
        logger.warning("No jobs returned from JSearch — database remains empty")
        return

    normalized = [_normalize(j) for j in raw_jobs]
    texts = [j["embedding_text"] for j in normalized]
    embeddings = await generate_embeddings_batch(texts)

    ingested = 0
    async with async_session() as db:
        for job, emb in zip(normalized, embeddings):
            logger.info(job["title"])
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
                    source=job["source"],
                    embedding=emb,
                )
            )
            ingested += 1
        await db.commit()

    logger.info("Seeded %d jobs into the database", ingested)
