"""Seed production (or any target DB) when the jobs table is empty.

Same behavior as the API startup hook ``seed_jobs_if_empty`` in ``seeder.py``, but run
standalone with an explicit DATABASE_URL — suitable for Cloud Run Jobs + Scheduler.

Environment (typical):

- DATABASE_URL — required. Cloud SQL unix socket example:
  postgresql+asyncpg://USER:PASS@/jobdb?host=/cloudsql/PROJECT:REGION:INSTANCE
- RAPIDAPI_KEY, GCP_PROJECT_ID — same as job-discovery service (Vertex + Pub/Sub).
- ADC: Workload Identity on Cloud Run or GOOGLE_APPLICATION_CREDENTIALS locally.

Local (repo root): set DATABASE_URL, then
PYTHONPATH=services python -m job_discovery_service.scripts.seed_production

Docker / Cloud Run Job: use the same image as job-discovery (services/job_discovery_service/Dockerfile)
but override the command, e.g.
python -m job_discovery_service.scripts.seed_production
(pass DATABASE_URL and other env the same way as the API service).

Exit: 0 on success or skip (table already has rows), 1 on failure.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

logger = logging.getLogger(__name__)


def _require_database_url() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print(
            "DATABASE_URL is required, e.g.\n"
            "  postgresql+asyncpg://USER:PASS@/jobdb?host=/cloudsql/PROJECT:REGION:INSTANCE",
            file=sys.stderr,
        )
        sys.exit(1)


async def _async_main() -> None:
    # Imported after env check so Settings binds to the intended database.
    from job_discovery_service.database import init_db
    from job_discovery_service.seeder import seed_jobs_if_empty

    await init_db()
    await seed_jobs_if_empty()


def main() -> None:
    _require_database_url()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s  %(name)s  %(message)s",
    )
    try:
        asyncio.run(_async_main())
    except SystemExit:
        raise
    except Exception:
        logger.exception("Production seed failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
