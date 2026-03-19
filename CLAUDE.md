# JobMatch — AI-Powered Job Matching Platform

A monorepo containing a full-stack job matching platform that uses pgvector similarity search to connect user profiles with job listings. Users authenticate with Google, fill out their profile, and receive ranked job matches computed asynchronously via vector cosine distance.

## Architecture Overview

```
┌──────────────┐       /api/user/*       ┌────────────────────┐
│              │ ──────────────────────►  │   User Service     │
│   Frontend   │                          │   (port 8002)      │
│  React/Vite  │       /api/jobs/*       ├────────────────────┤
│  (port 3000) │ ──────────────────────►  │ Job Discovery Svc  │
│              │                          │   (port 8001)      │
└──────────────┘                          └─────────┬──────────┘
                                                    │
                          ┌─────────────────────────┼─────────────────────────┐
                          │            Pub/Sub       │                         │
                          │                          ▼                         │
                          │  user-refresh-requested       matches-calculated   │
                          │  User Service ──────────►  Job Discovery ────────► │
                          │                          User Service              │
                          └────────────────────────────────────────────────────┘
                                                    │
                                          ┌─────────▼──────────┐
                                          │   PostgreSQL 16    │
                                          │   + pgvector       │
                                          │   (port 5432)      │
                                          │                    │
                                          │  Tables:           │
                                          │   jobs             │
                                          │   users            │
                                          │   user_matches     │
                                          └────────────────────┘
```

## Repository Structure

```
big-data-project/
├── CLAUDE.md                          ← This file
├── .env                               ← Shared environment variables (credentials, config)
├── docker-compose.yml                 ← All 4 services: postgres, job-discovery, user, frontend
│
├── services/
│   ├── job_discovery_service/         ← Job storage, vector search, Pub/Sub matching worker
│   │   ├── SERVICE.md                 ← Detailed service documentation
│   │   ├── main.py                    ← FastAPI entrypoint
│   │   ├── config.py                  ← Pydantic Settings
│   │   ├── database.py                ← Async SQLAlchemy + pgvector extension init
│   │   ├── models.py                  ← Job model with Vector(768) + HNSW index
│   │   ├── schemas.py                 ← Pydantic models (REST + Pub/Sub contracts)
│   │   ├── api/router.py              ← GET /jobs/{id}, POST /jobs/search, POST /internal/ingest
│   │   ├── api/dependencies.py        ← DB session + internal key guard
│   │   ├── worker/embedder.py         ← LangChain + Vertex AI embedding generation
│   │   ├── worker/processor.py        ← Pub/Sub subscriber → vector search → publish results
│   │   ├── scripts/cron_fetcher.py    ← JSearch RapidAPI ingestion script
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── user_service/                  ← User profiles, auth, event dispatch, match history
│       ├── SERVICE.md                 ← Detailed service documentation
│       ├── main.py                    ← FastAPI entrypoint
│       ├── config.py                  ← Pydantic Settings
│       ├── database.py                ← Async SQLAlchemy + pgvector extension init
│       ├── models.py                  ← User + UserMatch models
│       ├── schemas.py                 ← Pydantic models (REST + Pub/Sub contracts)
│       ├── embedder.py                ← LangChain profile → vector embedding
│       ├── api/routes.py              ← GET /me, PATCH /me, GET /me/matches
│       ├── api/auth.py                ← Firebase UID header validation
│       ├── messaging/publisher.py     ← Publishes to user-refresh-requested
│       ├── messaging/subscriber.py    ← Subscribes to matches-calculated
│       ├── requirements.txt
│       └── Dockerfile
│
├── frontend/                          ← React SPA with Google sign-in
│   ├── SERVICE.md                     ← Detailed service documentation
│   ├── .env.local                     ← Firebase config (VITE_FIREBASE_*)
│   ├── vite.config.ts                 ← Tailwind v4 + dev proxy config
│   ├── nginx.conf                     ← Production reverse proxy
│   ├── Dockerfile                     ← Multi-stage: node build → nginx
│   └── src/
│       ├── firebase.ts                ← Firebase init + GoogleAuthProvider
│       ├── contexts/AuthContext.tsx    ← Auth state + sign-in/sign-out
│       ├── api/client.ts              ← Typed fetch wrapper (injects X-Firebase-UID)
│       ├── pages/Login.tsx            ← Google sign-in page
│       ├── pages/Dashboard.tsx        ← Profile editor + match results
│       ├── components/ProfileForm.tsx ← Skills tags, salary, remote toggle
│       ├── components/MatchList.tsx   ← Job cards with Apply links
│       └── types.ts                   ← Shared TypeScript interfaces
│
├── gateway/                           ← API gateway config (placeholder)
│   └── openapi.yml
│
└── intrastructure/                    ← GCP infra-as-code (placeholder)
```

## Core Data Flow

### 1. Job Ingestion

`cron_fetcher.py` runs on a schedule and populates the database:

JSearch RapidAPI → normalize fields → LangChain/Vertex AI embedding (768-dim) → PostgreSQL `jobs` table

### 2. User Profile Update

When a user saves their profile via the frontend:

PATCH /me → save to `users` table → generate profile embedding via LangChain → set `needs_refresh=true` → publish to `user-refresh-requested` Pub/Sub topic → return 200 OK immediately

### 3. Asynchronous Matching

The Job Discovery Service subscriber picks up the message:

Receive `{user_id, user_vector, filters}` → query `jobs` table with `ORDER BY embedding <=> user_vector` + metadata filters → collect top 10 job IDs → publish to `matches-calculated` topic

### 4. Match Persistence

The User Service subscriber picks up the result:

Receive `{user_id, matched_job_ids, timestamp}` → insert into `user_matches` table → set `needs_refresh=false` on user

### 5. Match Display

The frontend fetches and displays results:

GET /me/matches → get job IDs → GET /jobs/{id} for each → render job cards with Apply links

## Tech Stack

| Layer        | Technology                                                        |
|--------------|-------------------------------------------------------------------|
| Frontend     | React 19, TypeScript, Vite 6, Tailwind CSS v4                    |
| Auth         | Firebase Authentication (Google sign-in)                          |
| API          | FastAPI with asyncio (both backend services)                      |
| Database     | PostgreSQL 16 + pgvector (HNSW index, cosine distance)            |
| ORM          | SQLAlchemy 2.0 async + asyncpg                                    |
| Embeddings   | LangChain + Vertex AI `text-embedding-004` (768 dimensions)       |
| Messaging    | GCP Pub/Sub (2 topics: user-refresh-requested, matches-calculated) |
| Job Source   | JSearch API via RapidAPI                                           |
| Containers   | Docker Compose (4 services)                                        |

## Database Tables

All three tables live in a single PostgreSQL database (`jobdb`):

- **`jobs`** — Job listings with title, company, description, location, salary, and a `VECTOR(768)` embedding column with an HNSW index. Owned by the Job Discovery Service.
- **`users`** — User profiles with bio, skills (PG array), preferences, a `VECTOR(768)` profile embedding, and a `needs_refresh` flag. Keyed by Firebase UID. Owned by the User Service.
- **`user_matches`** — Match history rows linking a user to an array of matched job IDs with a timestamp. Owned by the User Service.

## Pub/Sub Topics

| Topic                      | Publisher         | Subscriber          | Payload                                    |
|----------------------------|-------------------|---------------------|--------------------------------------------|
| `user-refresh-requested`   | User Service      | Job Discovery Svc   | `{user_id, user_vector, filters}`          |
| `matches-calculated`       | Job Discovery Svc | User Service         | `{user_id, matched_job_ids, timestamp}`    |

## API Surface

### User Service (port 8002)

All endpoints require `X-Firebase-UID` header.

| Method  | Path          | Purpose                                                  |
|---------|---------------|----------------------------------------------------------|
| GET     | /me           | Get or lazy-create user profile                          |
| PATCH   | /me           | Update profile → re-embed → publish refresh event        |
| GET     | /me/matches   | Get latest match results                                 |
| GET     | /health       | Health check                                             |

### Job Discovery Service (port 8001)

| Method  | Path              | Purpose                                              |
|---------|-------------------|------------------------------------------------------|
| GET     | /jobs/{id}        | Get a single job by ID                               |
| POST    | /jobs/search      | Hybrid vector + metadata search                      |
| POST    | /internal/ingest  | Bulk insert jobs (requires X-Internal-Key header)    |
| GET     | /health           | Health check                                         |

## Credentials Required

| Credential                 | Location              | Purpose                                     |
|----------------------------|-----------------------|---------------------------------------------|
| Firebase config (6 values) | `frontend/.env.local` | Google sign-in in the browser               |
| `GCP_PROJECT_ID`           | `.env`                | Vertex AI embeddings + Pub/Sub              |
| GCP ADC                    | System-level          | `gcloud auth application-default login`     |
| `RAPIDAPI_KEY`             | `.env`                | JSearch API for job ingestion               |
| `INTERNAL_API_KEY`         | `.env`                | Guards the /internal/ingest endpoint        |

## Quick Start

```bash
# 1. Fill in credentials
#    - Set GCP_PROJECT_ID in .env
#    - Set RAPIDAPI_KEY in .env (for job fetching)
#    - Fill in VITE_FIREBASE_* values in frontend/.env.local
#    - Run: gcloud auth application-default login

# 2. Start everything
docker compose up --build

# 3. Access
#    Frontend:           http://localhost:3000
#    User Service docs:  http://localhost:8002/docs
#    Job Discovery docs: http://localhost:8001/docs

# 4. Ingest jobs (run once, or on a schedule)
cd services/job_discovery_service
python -m job_discovery_service.scripts.cron_fetcher
```

## Per-Service Documentation

Each service has its own `SERVICE.md` with detailed coverage of schemas, endpoints, environment variables, and internal logic:

- `services/job_discovery_service/SERVICE.md`
- `services/user_service/SERVICE.md`
- `frontend/SERVICE.md`
