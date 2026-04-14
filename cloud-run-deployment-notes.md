# Cloud Run Deployment Takeaways

## 1. Postgres DATABASE_URL Format

Always use the driver prefix that matches your async library:

```
postgresql+asyncpg://USERNAME:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE
```

- `+asyncpg` tells SQLAlchemy to use asyncpg and never fall back to psycopg2
- For Cloud SQL, the host is a Unix socket path, not an IP address
- `localhost` / IP only applies for direct connections (not recommended for Cloud Run)

### How to find your values

```bash
# Find instance name
gcloud sql instances list --project=YOUR_PROJECT

# Find users
gcloud sql users list --instance=INSTANCE_NAME --project=YOUR_PROJECT

# Find databases
gcloud sql databases list --instance=INSTANCE_NAME --project=YOUR_PROJECT

# Reset a password if forgotten
gcloud sql users set-password USERNAME \
  --instance=INSTANCE_NAME \
  --project=YOUR_PROJECT \
  --password=newpassword
```

---

## 2. Monorepo Docker Structure (Best Practice)

### Recommended directory layout

```
my-repo/
├── .dockerignore
├── services/
│   ├── job_discovery_service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── __init__.py
│   │   └── main.py, models.py, database.py, api/...
│   └── another_service/
│       ├── Dockerfile
│       └── ...
```

### Dockerfile (lives inside the service folder)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY services/job_discovery_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/job_discovery_service ./job_discovery_service

ENV PORT=8080

CMD uvicorn job_discovery_service.main:app --host 0.0.0.0 --port 8080
```

### Always build from repo root

```bash
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t us-central1-docker.pkg.dev/PROJECT/REPO/service_name:latest \
  -f services/job_discovery_service/Dockerfile \
  --load \
  .
```

**Why repo root?**
- Docker build context determines what files are visible to COPY
- Building from root lets you copy shared code across services
- CI/CD pipelines always run from root
- Use `-f` to point at the Dockerfile inside the service subfolder

### Why relative imports break (and how to fix it)

When you build from `services/job_discovery_service/`, Docker copies files flat:
```
/app/main.py      ← no package folder
/app/models.py
```
So `from .api.router import router` fails — there's no parent package.

When you build from repo root and `COPY services/job_discovery_service ./job_discovery_service`:
```
/app/job_discovery_service/main.py    ← package exists
/app/job_discovery_service/models.py
```
Relative imports work correctly.

### .dockerignore (repo root)

```
**/__pycache__
**/.env
**/*.pyc
.git
**/node_modules
```

---

## 3. Environment Variables on Cloud Run

### How it works

- Cloud Run has its own env var system — set at deploy time or via the console
- `os.environ` works perfectly and reads Cloud Run env vars
- `load_dotenv()` silently does nothing on Cloud Run (no `.env` file exists) — harmless but pointless
- Never copy `.env` files into your Docker image

### Setting env vars at deploy time

```bash
gcloud run deploy SERVICE_NAME \
  --set-env-vars="KEY=value,ANOTHER_KEY=value"
```

### Updating env vars without redeploying image

```bash
gcloud run services update SERVICE_NAME \
  --region=REGION \
  --set-env-vars="KEY=newvalue"
```

### Using Secret Manager (recommended for passwords)

```bash
gcloud run deploy SERVICE_NAME \
  --set-secrets="DATABASE_URL=database-url:latest"
```

---

## 4. Full Deploy Command (Cloud Run + Cloud SQL)

```bash
# 1. Build
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t us-central1-docker.pkg.dev/PROJECT/REPO/service_name:latest \
  -f services/job_discovery_service/Dockerfile \
  --load \
  .

# 2. Push
docker push us-central1-docker.pkg.dev/PROJECT/REPO/service_name:latest

# 3. Deploy
gcloud run deploy SERVICE_NAME \
  --project=PROJECT_ID \
  --region=REGION \
  --image=us-central1-docker.pkg.dev/PROJECT/REPO/service_name:latest \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE_NAME \
  --set-env-vars="DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE_NAME"
```

---

## 5. Debugging Cloud Run Failures

When Cloud Run says "container failed to start", always check logs first:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="YOUR_SERVICE"' \
  --project=YOUR_PROJECT \
  --limit=50 \
  --format="value(textPayload)"
```

### Common failure causes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'your_service'` | Wrong build context, package folder not in container | Build from repo root, use `COPY services/x ./x` |
| `ImportError: attempted relative import with no known parent package` | Same as above | Same fix |
| `ModuleNotFoundError: No module named 'psycopg2'` | SQLAlchemy using wrong driver | Use `postgresql+asyncpg://` in DATABASE_URL |
| `Permission denied` | Cloud Run service account missing IAM role | Grant `roles/secretmanager.secretAccessor`, `roles/cloudsql.client`, etc. |
| App crashes on startup | Missing env var | Add `--set-env-vars` to deploy command |
