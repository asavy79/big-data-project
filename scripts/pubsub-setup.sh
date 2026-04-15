#!/usr/bin/env bash
# Starts the Pub/Sub emulator and pre-creates the topics + subscriptions
# that the User Service and Job Discovery Service expect.
set -e

PROJECT_ID="${GCP_PROJECT_ID:-local-project}"
PORT="8085"

gcloud beta emulators pubsub start \
  --host-port="0.0.0.0:${PORT}" \
  --project="${PROJECT_ID}" &
PID=$!

echo "Waiting for Pub/Sub emulator on port ${PORT}..."
until curl -s "http://localhost:${PORT}" > /dev/null 2>&1; do
  sleep 1
done
echo "Emulator started."

echo "Creating topics and subscriptions..."

curl -s -X PUT \
  "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/topics/user-refresh-requested"
curl -s -X PUT \
  "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/topics/matches-calculated"
curl -s -X PUT \
  "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/topics/jobs-ingested"

# Push (default, matches docker-compose + Cloud Run) or pull-only for local host-run services.
if [ "${PUBSUB_USE_PUSH_SUBSCRIPTIONS:-true}" = "true" ]; then
  MATCH_PUSH="${MATCHING_SERVICE_PUSH_URL:-http://matching-service:8000/internal/pubsub/user-refresh}"
  INGEST_PUSH="${MATCHING_SERVICE_JOBS_INGESTED_PUSH_URL:-http://matching-service:8000/internal/pubsub/jobs-ingested}"
  USER_MATCH_PUSH="${USER_SERVICE_MATCHES_PUSH_URL:-http://user-service:8000/internal/pubsub/matches-calculated}"

  curl -s -X PUT \
    "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/subscriptions/user-refresh-requested-sub" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${PROJECT_ID}/topics/user-refresh-requested\", \"pushConfig\": {\"pushEndpoint\": \"${MATCH_PUSH}\"}}"

  curl -s -X PUT \
    "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/subscriptions/matches-calculated-sub" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${PROJECT_ID}/topics/matches-calculated\", \"pushConfig\": {\"pushEndpoint\": \"${USER_MATCH_PUSH}\"}}"

  curl -s -X PUT \
    "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/subscriptions/jobs-ingested-sub" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${PROJECT_ID}/topics/jobs-ingested\", \"pushConfig\": {\"pushEndpoint\": \"${INGEST_PUSH}\"}}"
else
  curl -s -X PUT \
    "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/subscriptions/user-refresh-requested-sub" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${PROJECT_ID}/topics/user-refresh-requested\"}"

  curl -s -X PUT \
    "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/subscriptions/matches-calculated-sub" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${PROJECT_ID}/topics/matches-calculated\"}"

  curl -s -X PUT \
    "http://localhost:${PORT}/v1/projects/${PROJECT_ID}/subscriptions/jobs-ingested-sub" \
    -H "Content-Type: application/json" \
    -d "{\"topic\": \"projects/${PROJECT_ID}/topics/jobs-ingested\"}"
fi

echo ""
echo "Pub/Sub emulator ready with topics and subscriptions."

wait $PID
