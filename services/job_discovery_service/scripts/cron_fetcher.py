"""Scheduled job-ingestion script — fetches from JSearch (RapidAPI).

Run locally:
    python -m job_discovery_service.scripts.cron_fetcher

Or deploy as a GCP Cloud Run Job on a cron schedule.

Flow:
  1. Query the JSearch API for recent postings
  2. Batch-generate embeddings via LangChain / Vertex AI
  3. Upsert new rows into PostgreSQL (skips duplicates by job_id)
"""

import asyncio
import logging
import sys
from pathlib import Path

import httpx
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings  # noqa: E402
from database import async_session, init_db  # noqa: E402
from models import Job  # noqa: E402
from worker.embedder import generate_embeddings_batch  # noqa: E402

logger = logging.getLogger(__name__)

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"


def _build_location(job: dict) -> str | None:
    city = job.get("job_city")
    state = job.get("job_state")
    country = job.get("job_country")
    parts = [p for p in (city, state, country) if p]
    return ", ".join(parts) if parts else None


def _build_embedding_text(job: dict) -> str:
    """Concatenate the most meaningful fields into a single string so the
    embedding captures title, responsibilities, and qualifications."""
    sections = [job.get("job_title", ""), job.get("job_description", "")]

    highlights = job.get("job_highlights") or {}
    for key in ("Qualifications", "Responsibilities"):
        items = highlights.get(key, [])
        if items:
            sections.append(f"{key}: " + "; ".join(items))

    return "\n".join(s for s in sections if s)


async def fetch_jobs(client: httpx.AsyncClient) -> list[dict]:
    """Page through the JSearch API and return the raw job dicts."""
    if not settings.rapidapi_key:
        logger.error("RAPIDAPI_KEY is not set — cannot fetch jobs")
        return []

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": settings.jsearch_host,
    }

    all_jobs: list[dict] = []

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

        data = resp.json()
        page_jobs = data.get("data", [])
        all_jobs.extend(page_jobs)
        logger.info("Page %d: fetched %d jobs", page, len(page_jobs))

    return all_jobs


def normalize_job(raw: dict) -> dict:
    """Map JSearch response fields to our Job model columns."""
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


async def ingest_jobs(normalized: list[dict]) -> int:
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
    return ingested


async def main() -> None:
    await init_db()

    async with httpx.AsyncClient() as client:
        raw_jobs = await fetch_jobs(client)

    logger.info("Fetched %d total jobs from JSearch", len(raw_jobs))

    normalized = [normalize_job(j) for j in raw_jobs]
    count = await ingest_jobs(normalized)
    logger.info("Ingested %d new jobs", count)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s"
    )
    asyncio.run(main())
