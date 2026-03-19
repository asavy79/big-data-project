from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Job
from ..schemas import (
    IngestResult,
    JobIngestRequest,
    JobResponse,
    JobSearchRequest,
    JobSearchResponse,
)
from ..worker.embedder import generate_embedding
from .dependencies import get_db, verify_internal

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "job-discovery"}


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(
    request: JobSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Hybrid search: vector similarity + metadata filters."""

    vector = request.user_vector
    if request.query and not vector:
        vector = await generate_embedding(request.query)

    if not vector:
        raise HTTPException(
            status_code=400, detail="Provide either user_vector or query"
        )

    query = select(Job).where(Job.embedding.is_not(None))

    f = request.filters
    # if f.location:
    #     query = query.where(Job.location.ilike(f"%{f.location}%"))
    # if f.remote is not None:
    #     query = query.where(Job.remote == f.remote)
    if f.salary_min is not None:
        query = query.where(Job.salary_max >= f.salary_min)
    if f.salary_max is not None:
        query = query.where(Job.salary_min <= f.salary_max)

    query = (
        query.order_by(Job.embedding.cosine_distance(vector)).limit(request.limit)
    )

    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobSearchResponse(jobs=jobs, total=len(jobs))


@router.post(
    "/internal/ingest",
    response_model=IngestResult,
    dependencies=[Depends(verify_internal)],
)
async def ingest_jobs(
    request: JobIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Bulk-insert jobs with auto-generated embeddings (service-to-service only)."""
    ingested = 0

    for item in request.jobs:
        exists = await db.execute(
            select(Job.id).where(Job.external_id == item.external_id)
        )
        if exists.scalar_one_or_none() is not None:
            continue

        embedding = await generate_embedding(item.description)

        job = Job(
            external_id=item.external_id,
            title=item.title,
            company=item.company,
            description=item.description,
            location=item.location,
            remote=item.remote,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            url=item.url,
            source=item.source,
            embedding=embedding,
        )
        db.add(job)
        ingested += 1

    await db.commit()
    return IngestResult(ingested=ingested, total_submitted=len(request.jobs))
