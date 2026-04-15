#!/bin/bash
# Create Pub/Sub topics and subscriptions for GCP.
#
# Scale-to-zero (Cloud Run): set push endpoints and deploy with PUBSUB_USE_PULL_SUBSCRIBER=false
#   export MATCHING_SERVICE_URL=https://your-matching-service-xxx.run.app
#   export USER_SERVICE_URL=https://your-user-service-xxx.run.app
#   ./scripts/pubsub-setup-prod.sh
#
# If MATCHING_SERVICE_URL / USER_SERVICE_URL are unset, creates *pull* subscriptions (legacy).

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-veerababu33}"

echo "Setting up Pub/Sub topics and subscriptions for project: $PROJECT_ID"

echo "Creating topics..."
gcloud pubsub topics create user-refresh-requested --project="$PROJECT_ID" 2>/dev/null || true
gcloud pubsub topics create jobs-ingested --project="$PROJECT_ID" 2>/dev/null || true
gcloud pubsub topics create matches-calculated --project="$PROJECT_ID" 2>/dev/null || true

if [ -n "${MATCHING_SERVICE_URL:-}" ] && [ -n "${USER_SERVICE_URL:-}" ]; then
  echo "Creating push subscriptions (Cloud Run)..."
  gcloud pubsub subscriptions create user-refresh-requested-sub \
    --topic=user-refresh-requested \
    --push-endpoint="${MATCHING_SERVICE_URL}/internal/pubsub/user-refresh" \
    --project="$PROJECT_ID" 2>/dev/null || true
  gcloud pubsub subscriptions create jobs-ingested-sub \
    --topic=jobs-ingested \
    --push-endpoint="${MATCHING_SERVICE_URL}/internal/pubsub/jobs-ingested" \
    --project="$PROJECT_ID" 2>/dev/null || true
  gcloud pubsub subscriptions create matches-calculated-sub \
    --topic=matches-calculated \
    --push-endpoint="${USER_SERVICE_URL}/internal/pubsub/matches-calculated" \
    --project="$PROJECT_ID" 2>/dev/null || true
  echo "Done. Ensure Pub/Sub can invoke Cloud Run (IAM invoker) and set PUBSUB_USE_PULL_SUBSCRIBER=false on services."
else
  echo "Creating pull subscriptions (set MATCHING_SERVICE_URL and USER_SERVICE_URL for push + scale-to-zero)..."
  gcloud pubsub subscriptions create user-refresh-requested-sub \
    --topic=user-refresh-requested \
    --project="$PROJECT_ID" 2>/dev/null || true
  gcloud pubsub subscriptions create jobs-ingested-sub \
    --topic=jobs-ingested \
    --project="$PROJECT_ID" 2>/dev/null || true
  gcloud pubsub subscriptions create matches-calculated-sub \
    --topic=matches-calculated \
    --project="$PROJECT_ID" 2>/dev/null || true
fi

echo "Done."
