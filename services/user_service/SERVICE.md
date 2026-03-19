# User Service

The identity and profile management layer of the JobMatch platform. This service owns user data, orchestrates the "Update & Notify" pattern (profile change → embed → Pub/Sub → match), and stores match results returned by the Job Discovery Service.

## Tech Stack

- **FastAPI** with asyncio for non-blocking HTTP
- **SQLAlchemy 2.0** (async) + **asyncpg** for database access
- **pgvector** for storing user profile embeddings (768 dimensions)
- **LangChain** + **Vertex AI** (`text-embedding-004`) for profile embedding generation
- **GCP Pub/Sub** for event-driven communication with the Job Discovery Service
- **Firebase Authentication** — the service trusts an `X-Firebase-UID` header forwarded by the API gateway

## Directory Structure

```
user_service/
├── main.py                  # FastAPI app with lifespan (init DB + start Pub/Sub subscriber)
├── app.py                   # Entry point alias for backwards compatibility
├── config.py                # Pydantic Settings — reads from environment / .env
├── database.py              # Async SQLAlchemy engine, session factory, init_db()
├── models.py                # User and UserMatch ORM models
├── schemas.py               # Pydantic models for REST API and Pub/Sub contracts
├── embedder.py              # LangChain profile → vector embedding generation
├── api/
│   ├── auth.py              # Firebase UID extraction + DB session dependency
│   └── routes.py            # Three user-facing routes + health check
├── messaging/
│   ├── publisher.py         # Publishes to user-refresh-requested topic
│   └── subscriber.py        # Subscribes to matches-calculated topic
├── requirements.txt
└── Dockerfile
```

## Database Schema

Two tables in the shared `jobdb` PostgreSQL database:

### `users`

| Column              | Type                      | Notes                                          |
|---------------------|---------------------------|-------------------------------------------------|
| `id`                | `VARCHAR` (PK)            | Firebase UID — set at creation                  |
| `email`             | `VARCHAR`                 |                                                 |
| `display_name`      | `VARCHAR`                 |                                                 |
| `bio`               | `TEXT`                    | Free-text profile description                   |
| `skills`            | `VARCHAR[]` (PG array)    | List of skill strings                           |
| `location`          | `VARCHAR`                 | Preferred work location                         |
| `remote_preference` | `BOOLEAN`                 | Default `true`                                  |
| `salary_min`        | `INTEGER`                 | Desired salary floor                            |
| `salary_max`        | `INTEGER`                 | Desired salary ceiling                          |
| `needs_refresh`     | `BOOLEAN`                 | `true` after profile change, cleared on match   |
| `embedding`         | `VECTOR(768)`             | Profile embedding (bio + skills + location)     |
| `created_at`        | `TIMESTAMPTZ`             | Server default `now()`                          |
| `updated_at`        | `TIMESTAMPTZ`             | Auto-updated on change                          |

### `user_matches`

| Column           | Type                      | Notes                                          |
|------------------|---------------------------|-------------------------------------------------|
| `id`             | `INTEGER` (PK, auto)      | Surrogate key                                   |
| `user_id`        | `VARCHAR` (FK → users.id) | Indexed                                         |
| `matched_job_ids`| `INTEGER[]` (PG array)    | List of matched job IDs from Job Discovery Svc  |
| `calculated_at`  | `TIMESTAMPTZ`             | When the Job Discovery Service ran the match     |
| `created_at`     | `TIMESTAMPTZ`             | When this row was persisted                      |

## API Endpoints

All endpoints require the `X-Firebase-UID` header (validated in `api/auth.py`).

| Method  | Path          | Description                                             |
|---------|---------------|---------------------------------------------------------|
| `GET`   | `/me`         | Retrieve profile — lazy-creates a new user if the Firebase UID is unseen |
| `PATCH` | `/me`         | Update profile fields → regenerate embedding → publish to Pub/Sub       |
| `GET`   | `/me/matches` | Fetch the 10 most recent match sets (job ID lists)                      |
| `GET`   | `/health`     | Health check for load balancers                                         |

### `PATCH /me` — Request Body

All fields are optional. Only provided fields are updated.

```json
{
  "display_name": "Alex Savard",
  "bio": "Full-stack engineer with 5 years in Python and React...",
  "skills": ["Python", "React", "PostgreSQL", "Docker"],
  "location": "Denver, CO",
  "remote_preference": true,
  "salary_min": 90000,
  "salary_max": 160000
}
```

### `GET /me/matches` — Response

```json
{
  "matches": [
    {
      "matched_job_ids": [101, 202, 303, 404, 505],
      "calculated_at": "2026-03-18T15:30:00Z"
    }
  ],
  "total": 1
}
```

## The "Update & Notify" Flow

This is the core workflow of the service:

1. **`PATCH /me`** — User updates skills, bio, location, or preferences
2. **`embedder.py`** — `build_profile_text()` concatenates display name + bio + skills + location into a single string. `generate_profile_embedding()` sends it through LangChain → Vertex AI → 768-dim vector. The vector is stored on `User.embedding`.
3. **`needs_refresh = True`** — Flag is set so a cleanup script can catch missed events.
4. **`publisher.py`** — Publishes `{user_id, user_vector, filters}` to the `user-refresh-requested` Pub/Sub topic.
5. **200 OK** — Returns immediately to the client. Matching happens asynchronously.
6. **Job Discovery Service** processes the message, runs pgvector similarity search, publishes results to `matches-calculated`.
7. **`subscriber.py`** — Picks up the match result, inserts a row into `user_matches`, and sets `needs_refresh = False`.
8. **`GET /me/matches`** — User (or frontend) fetches the updated match list.

## Pub/Sub Messaging

### Publishes to: `user-refresh-requested`

Triggered on every `PATCH /me` that changes profile fields.

**Outgoing payload:**

```json
{
  "user_id": "firebase-uid-string",
  "user_vector": [0.12, -0.4, ...],
  "filters": {
    "location": "Denver, CO",
    "remote": true,
    "salary_min": 90000,
    "salary_max": null
  }
}
```

### Subscribes to: `matches-calculated`

Receives match results from the Job Discovery Service.

**Incoming payload:**

```json
{
  "user_id": "firebase-uid-string",
  "matched_job_ids": [101, 202, 303],
  "timestamp": "2026-03-18T15:30:00Z"
}
```

**Processing:** Validates the user exists, inserts a `UserMatch` row, and clears the `needs_refresh` flag.

## Profile Embedding

`embedder.py` generates a user profile vector using the same embedding model and dimensionality as the Job Discovery Service, ensuring cosine distance between user and job vectors is meaningful.

**Text construction (`build_profile_text`):**
```
Alex Savard
Full-stack engineer with 5 years in Python and React...
Skills: Python, React, PostgreSQL, Docker
Location: Denver, CO
```

If the user has no profile text yet, a zero vector is returned to avoid API errors.

## Authentication

`api/auth.py` extracts the `X-Firebase-UID` header from each request. In the current implementation, it trusts the header as-is (suitable when an API gateway validates the Firebase ID token upstream).

For direct-to-service deployment, swap in Firebase Admin SDK verification:
```python
firebase_admin.auth.verify_id_token(token)
```

## Environment Variables

| Variable                     | Required | Default                       | Purpose                                 |
|------------------------------|----------|-------------------------------|-----------------------------------------|
| `DATABASE_URL`               | Yes      | `postgresql+asyncpg://...`    | Async Postgres connection string        |
| `GCP_PROJECT_ID`             | Yes*     | `""`                          | GCP project for Vertex AI + Pub/Sub     |
| `VERTEX_AI_LOCATION`         | No       | `us-central1`                 | Vertex AI region                        |
| `EMBEDDING_MODEL`            | No       | `text-embedding-004`          | LangChain embedding model name          |
| `PUBSUB_TOPIC_REFRESH`       | No       | `user-refresh-requested`      | Topic to publish profile change events  |
| `PUBSUB_SUBSCRIPTION_MATCHES`| No       | `matches-calculated-sub`      | Subscription for incoming match results |

*Required for full functionality. Without it, Pub/Sub and embeddings are disabled.

GCP authentication uses Application Default Credentials (ADC) — run `gcloud auth application-default login` locally.

## Running

```bash
# Local (with Postgres already running)
uvicorn user_service.main:app --host 0.0.0.0 --port 8000

# Docker Compose (from repo root)
docker compose up user-service
```

Swagger docs available at `http://localhost:8002/docs` when running via Docker Compose.
