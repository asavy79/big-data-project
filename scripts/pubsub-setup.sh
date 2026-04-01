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

echo ""
echo "Pub/Sub emulator ready with topics and subscriptions."

wait $PID
