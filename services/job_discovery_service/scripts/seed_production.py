"""Fetch jobs from JSearch and insert into the DB (standalone).

Always runs a **force** seed: pulls from JSearch even if the table already has rows.
Rows with the same ``external_id`` as an existing job are skipped.

Tune volume and filters via env (same as job-discovery service):

- ``JSEARCH_QUERY`` — default targets data science / ML roles in the US.
- ``JSEARCH_DATE_POSTED`` — use ``month`` for roughly the last month (JSearch values:
  ``all``, ``today``, ``3days``, ``week``, ``month``).
- ``JSEARCH_NUM_PAGES`` — pages 1..N (max 50); ~10 jobs per page per RapidAPI.

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

Exit: 0 on success (including 0 new inserts if everything was duplicate), 1 on failure.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys

logger = logging.getLogger(__name__)


def _require_database_url() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print(
            "DATABASE_URL is required.\n"
            "  Local Docker Postgres:\n"
            "    export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobdb\n"
            "  Cloud Run / Cloud SQL socket:\n"
            "    postgresql+asyncpg://USER:PASS@/jobdb?host=/cloudsql/PROJECT:REGION:INSTANCE",
            file=sys.stderr,
        )
        sys.exit(1)

    # Cloud SQL unix socket: only exists on GCP or when Cloud SQL Auth Proxy is running.
    m = re.search(r"host=([^&]+)", url)
    if m:
        sock = m.group(1)
        if sock.startswith("/cloudsql") and not os.path.exists(sock):
            print(
                "DATABASE_URL uses a Cloud SQL socket at:\n"
                f"  {sock}\n"
                "That path does not exist on this machine. It only exists inside GCP (Cloud Run) "
                "or after starting the Cloud SQL Auth Proxy (which creates /cloudsql/...).\n\n"
                "For a local seed against Docker Postgres:\n"
                "  export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobdb\n"
                "  docker compose up -d postgres\n",
                file=sys.stderr,
            )
            sys.exit(1)


async def _async_main() -> None:
    # Imported after env check so Settings binds to the intended database.
    from job_discovery_service.database import init_db
    from job_discovery_service.seeder import seed_jobs

    await init_db()
    await seed_jobs(force=True)


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
