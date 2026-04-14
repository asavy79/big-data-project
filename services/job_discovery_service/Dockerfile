FROM python:3.12-slim

WORKDIR /app

COPY services/job_discovery_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install as a package tree so relative imports in main.py work (same pattern as user_service).
COPY services/job_discovery_service ./job_discovery_service

ENV PORT=8080

CMD sh -c "uvicorn job_discovery_service.main:app --host 0.0.0.0 --port ${PORT}"
