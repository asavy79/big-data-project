# Job Discovery Service

The search and matching engine of the JobMatch platform. This service stores job listings in PostgreSQL with pgvector embeddings, performs hybrid vector + metadata search, and processes asynchronous match requests from the User Service via GCP Pub/Sub.

## Tech Stack

- **FastAPI** with asyncio for non-blocking HTTP and background workers
- **SQLAlchemy 2.0** (async) + **asyncpg** for database access
- **pgvector** for 768-dimensional vector storage and HNSW-indexed cosine similarity search
- **LangChain** + **Vertex AI** (`text-embedding-004`) for embedding generation
- **GCP Pub/Sub** for event-driven communication with the User Service
- **JSearch (RapidAPI)** for sourcing real job listings

## Directory Structure

```
job_discovery_service/
├── main.py                  # FastAPI app with lifespan (init DB + start Pub/Sub subscriber)
├── config.py                # Pydantic Settings — reads from environment / .env
├── database.py              # Async SQLAlchemy engine, session factory, init_db()
├── models.py                # Job ORM model with pgvector embedding column + HNSW index
├── schemas.py               # Pydantic models for REST API and Pub/Sub message contracts
├── api/
│   ├── router.py            # Four route handlers (health, get job, search, ingest)
│   └── dependencies.py      # FastAPI dependencies: DB session injection, internal key guard
├── worker/
│   ├── embedder.py          # LangChain VertexAIEmbeddings wrapper (single + batch)
│   └── processor.py         # Pub/Sub subscriber: receives match requests, runs vector search, publishes results
├── scripts/
│   └── cron_fetcher.py      # Standalone script to fetch jobs from JSearch API and ingest them
├── requirements.txt
└── Dockerfile
```

## Database Schema

Single table in the shared `jobdb` PostgreSQL database:

### `jobs`

| Column        | Type                      | Notes                                         |
|---------------|---------------------------|-----------------------------------------------|
| `id`          | `INTEGER` (PK, auto)      | Internal surrogate key                        |
| `external_id` | `VARCHAR` (unique, indexed)| Source-specific ID (e.g. JSearch `job_id`)    |
| `title`       | `VARCHAR` (not null)       |                                               |
| `company`     | `VARCHAR` (not null)       |                                               |
| `description` | `TEXT`                     | Full job description                          |
| `location`    | `VARCHAR`                  | City, State, Country                          |
| `remote`      | `BOOLEAN`                  | Default `false`                               |
| `salary_min`  | `INTEGER`                  | Annual salary floor                           |
| `salary_max`  | `INTEGER`                  | Annual salary ceiling                         |
| `url`         | `VARCHAR`                  | Apply link                                    |
| `source`      | `VARCHAR`                  | e.g. `"jsearch"`                              |
| `embedding`   | `VECTOR(768)`              | Vertex AI text-embedding-004 output           |
| `created_at`  | `TIMESTAMPTZ`              | Server default `now()`                        |
| `updated_at`  | `TIMESTAMPTZ`              | Auto-updated on change                        |

An **HNSW index** (`ix_jobs_embedding_hnsw`) is created on the `embedding` column with `vector_cosine_ops` for sub-millisecond similarity search at scale.

## API Endpoints

| Method | Path               | Auth              | Description                                              |
|--------|--------------------|-------------------|----------------------------------------------------------|
| `GET`  | `/health`          | None              | Health check for load balancers                          |
| `GET`  | `/jobs/{job_id}`   | None              | Fetch a single job's metadata by internal ID             |
| `POST` | `/jobs/search`     | None              | Hybrid search: vector similarity + metadata filters      |
| `POST` | `/internal/ingest` | `X-Internal-Key`  | Bulk insert jobs with auto-generated embeddings          |

### `POST /jobs/search` — Request Body

```json
{
  "user_vector": [0.12, -0.4, ...],   // 768-dim float array (optional if query is provided)
  "query": "senior python engineer",   // plain text — auto-embedded if user_vector is absent
  "filters": {
    "location": "Denver",
    "remote": true,
    "salary_min": 80000,
    "salary_max": 200000
  },
  "limit": 10
}
```

The search applies metadata filters first, then orders by `cosine_distance(embedding, user_vector)` and returns the top N results.

### `POST /internal/ingest` — Request Body

Protected by the `X-Internal-Key` header. Used by the cron fetcher or other services to bulk-insert jobs.

```json
{
  "jobs": [
    {
      "external_id": "abc123",
      "title": "Backend Engineer",
      "company": "Acme Inc",
      "description": "Full job description text...",
      "location": "Austin, TX",
      "remote": false,
      "salary_min": 90000,
      "salary_max": 140000,
      "url": "https://example.com/apply",
      "source": "jsearch"
    }
  ]
}
```

Each job's `description` is passed through LangChain → Vertex AI to generate the embedding before insertion. Duplicates (by `external_id`) are skipped.

## Pub/Sub Messaging

### Subscribes to: `user-refresh-requested`

Triggered when the User Service sends a match request after a profile update.

**Incoming payload:**

```json
{
  "user_id": "firebase-uid-string",
  "user_vector": [0.12, -0.4, ...],
  "filters": { "location": "Denver", "remote": true }
}
```

**Processing:** The `worker/processor.py` subscriber runs a pgvector similarity query against the `jobs` table using `ORDER BY embedding <=> user_vector`, applies metadata filters, and collects the top 10 job IDs.

### Publishes to: `matches-calculated`

Fired immediately after matching completes.

**Outgoing payload:**

```json
{
  "user_id": "firebase-uid-string",
  "matched_job_ids": [101, 202, 303],
  "timestamp": "2026-03-18T15:30:00Z"
}
```

The User Service picks this up and persists the results into its `user_matches` table.

## Job Ingestion (Cron Fetcher)

`scripts/cron_fetcher.py` is a standalone async script designed to run on a schedule (locally or as a GCP Cloud Run Job).

**Flow:**
1. Calls the JSearch RapidAPI (`jsearch.p.rapidapi.com/search`) with configurable query, date range, and page count
2. Normalizes JSearch response fields → Job model fields (`job_title` → `title`, `employer_name` → `company`, etc.)
3. Builds a rich embedding text from `job_title` + `job_description` + `Qualifications` + `Responsibilities`
4. Batch-generates embeddings via LangChain / Vertex AI
5. Upserts into PostgreSQL, skipping duplicates by `external_id`

**Run locally:**
```bash
python -m job_discovery_service.scripts.cron_fetcher
```

## Embedding Generation

`worker/embedder.py` wraps `langchain-google-vertexai.VertexAIEmbeddings` with lazy initialization. The same model instance is reused across all calls.

- `generate_embedding(text)` — single text → 768-dim vector
- `generate_embeddings_batch(texts)` — list of texts → list of vectors

Both are async and used by the API router (for search-by-query and ingest) and the cron fetcher.

## Environment Variables

| Variable              | Required | Default                          | Purpose                              |
|-----------------------|----------|----------------------------------|--------------------------------------|
| `DATABASE_URL`        | Yes      | `postgresql+asyncpg://...`       | Async Postgres connection string     |
| `GCP_PROJECT_ID`      | Yes*     | `""`                             | GCP project for Vertex AI + Pub/Sub  |
| `VERTEX_AI_LOCATION`  | No       | `us-central1`                    | Vertex AI region                     |
| `EMBEDDING_MODEL`     | No       | `text-embedding-004`             | LangChain embedding model name       |
| `RAPIDAPI_KEY`        | Yes*     | `""`                             | JSearch API key                      |
| `JSEARCH_QUERY`       | No       | `software engineer in US`        | Default search query                 |
| `JSEARCH_DATE_POSTED` | No       | `3days`                          | JSearch date filter                  |
| `JSEARCH_NUM_PAGES`   | No       | `1`                              | Pages to fetch per cron run          |
| `INTERNAL_API_KEY`    | No       | `changeme`                       | Guards `/internal/ingest`            |
| `PUBSUB_SUBSCRIPTION` | No       | `user-refresh-requested-sub`     | Pub/Sub subscription name            |
| `PUBSUB_TOPIC_MATCHES`| No       | `matches-calculated`             | Pub/Sub topic to publish results     |

*Required for full functionality. The service starts without them but disables Pub/Sub and embedding generation.

GCP authentication uses Application Default Credentials (ADC) — run `gcloud auth application-default login` locally.

## Running

```bash
# Local (with Postgres already running)
uvicorn job_discovery_service.main:app --host 0.0.0.0 --port 8000

# Docker Compose (from repo root)
docker compose up job-discovery-service
```

Swagger docs available at `http://localhost:8001/docs` when running via Docker Compose.
