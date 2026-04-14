#!/usr/bin/env bash
set -euo pipefail

# Edit these, then run: ./scripts/deploy-job-discovery.sh
# One-time: gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
PROJECT_ID="veerababu33"
REGION="us-central1"
REPOSITORY="service-repo"
TAG="latest"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/job_discovery_service:${TAG}"

export BUILDX_NO_DEFAULT_ATTESTATIONS=1

docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -f "${ROOT}/services/job_discovery_service/Dockerfile" \
  -t "${IMAGE}" \
  --load \
  "${ROOT}"

docker push "${IMAGE}"

gcloud run deploy job-discovery-service \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}"
