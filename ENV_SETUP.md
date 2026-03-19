# Environment Variables

This project requires two environment files. Copy the examples below, fill in the values, and never commit the real files to Git.

---

## Root `.env`

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

| Variable | Required | Description | Example |
|---|---|---|---|
| `POSTGRES_USER` | Yes | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | Yes | PostgreSQL database name | `jobdb` |
| `DATABASE_URL` | Yes | Async connection string (used by services) | `postgresql+asyncpg://postgres:postgres@localhost:5432/jobdb` |
| `GCP_PROJECT_ID` | Yes | Google Cloud project ID (for Vertex AI + Pub/Sub) | `my-gcp-project` |
| `VERTEX_AI_LOCATION` | No | Vertex AI region (default: `us-central1`) | `us-central1` |
| `EMBEDDING_MODEL` | No | Vertex AI embedding model (default: `text-embedding-004`) | `text-embedding-004` |
| `PUBSUB_SUBSCRIPTION` | No | Pub/Sub subscription for job-discovery worker | `user-refresh-requested-sub` |
| `PUBSUB_TOPIC_MATCHES` | No | Topic the job-discovery service publishes match results to | `matches-calculated` |
| `PUBSUB_TOPIC_REFRESH` | No | Topic the user service publishes refresh requests to | `user-refresh-requested` |
| `PUBSUB_SUBSCRIPTION_MATCHES` | No | Pub/Sub subscription for user service match listener | `matches-calculated-sub` |
| `RAPIDAPI_KEY` | Yes | RapidAPI key for JSearch job fetching | `your-rapidapi-key` |
| `JSEARCH_QUERY` | No | Default JSearch query (default: `software engineer in United States`) | `data engineer in Canada` |
| `JSEARCH_DATE_POSTED` | No | JSearch date filter (default: `3days`) | `week` |
| `JSEARCH_NUM_PAGES` | No | Number of JSearch result pages to fetch (default: `1`) | `3` |
| `INTERNAL_API_KEY` | Yes | Shared secret for service-to-service `/internal/ingest` calls | `some-random-secret` |
| `DEV_MODE` | No | Enable dev-mode bypasses (default: `true`) | `true` |

---

## Frontend `frontend/.env.local`

Create a `.env.local` file in the `frontend/` directory:

| Variable | Required | Description | Where to find it |
|---|---|---|---|
| `VITE_FIREBASE_API_KEY` | Yes | Firebase Web API key | Firebase Console → Project Settings → Your Apps |
| `VITE_FIREBASE_AUTH_DOMAIN` | Yes | Firebase Auth domain | Same location, `authDomain` field |
| `VITE_FIREBASE_PROJECT_ID` | Yes | Firebase project ID | Same location, `projectId` field |
| `VITE_FIREBASE_STORAGE_BUCKET` | Yes | Firebase Storage bucket | Same location, `storageBucket` field |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Yes | Firebase Cloud Messaging sender ID | Same location, `messagingSenderId` field |
| `VITE_FIREBASE_APP_ID` | Yes | Firebase app ID | Same location, `appId` field |

### How to get Firebase values

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create one)
3. Click the gear icon → **Project settings**
4. Scroll to **Your apps** → select your Web app (or **Add app** → Web)
5. Copy the config values from the `firebaseConfig` object

You also need to enable Google sign-in:
1. In the Firebase Console, go to **Authentication → Sign-in method**
2. Click **Google** and toggle **Enable**

---

## GCP Authentication

The backend services use Google Cloud Application Default Credentials (ADC) for Vertex AI embeddings and Pub/Sub. Run this once on your local machine:

```bash
gcloud auth application-default login
```

This creates `~/.config/gcloud/application_default_credentials.json`, which Docker Compose mounts into the containers automatically.

---

## Quick Start

```bash
# 1. Copy and fill in environment files
cp .env.example .env          # then edit with your values
# Create frontend/.env.local   # then add Firebase config

# 2. Authenticate with GCP
gcloud auth application-default login

# 3. Start all services
docker compose up --build
```
