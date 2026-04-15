#!/usr/bin/env bash
set -euo pipefail

# Build, push, and roll Cloud Run for the three backend services.
#
# You already have: Artifact Registry repo, Cloud SQL Postgres, frontend deployed.
# This script only ships new container images. It does not set DATABASE_URL,
# secrets, VPC connector, or IAM — configure those once on each Cloud Run service
# (console or gcloud) after you point them at your new database.
#
# Usage:
#   export PROJECT_ID=your-gcp-project-id
#   ./scripts/deploy-services.sh
#
# Optional env overrides:
#   REGION=us-central1 REPOSITORY=service-repo IMAGE_TAG=2026-04-13 ./scripts/deploy-services.sh
#
# Cloud Run runs linux/amd64. On Apple Silicon, Docker defaults to arm64 — builds fail unless
# you target amd64 (set below). Builds may be slower due to emulation.
#
# Docker BuildKit can attach provenance/SBOM attestations; that produces an OCI *index* manifest
# that Cloud Run rejects ("must support amd64/linux") even for amd64 images. We disable those.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"

# Build from repo root; Dockerfiles use COPY services/<name>/...
docker_build_cloudrun() {
  local tag="$1"
  local dockerfile="$2"
  local context="$3"
  docker buildx build \
    --platform "${DOCKER_PLATFORM}" \
    --provenance=false \
    --sbom=false \
    -f "${dockerfile}" \
    -t "${tag}" \
    --load \
    "${context}"
}

# Must be the GCP project *id* (e.g. my-project-123), not an email. No @ character.
: "${PROJECT_ID:?Set PROJECT_ID to your GCP project id (gcloud config get-value project)}"
if [[ "${PROJECT_ID}" == *"@"* ]] || [[ "${PROJECT_ID}" == *"/"* ]]; then
  echo "ERROR: PROJECT_ID looks wrong (found @ or /). Use your GCP project id, not an email."
  exit 1
fi

REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-service-repo}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

AR_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}"
SERVICES=(job_discovery_service user_service matching_service)

echo "==> Docker auth for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Stops BuildKit from attaching attestations that become an OCI index (Cloud Run rejects that).
export BUILDX_NO_DEFAULT_ATTESTATIONS=1

echo "==> Building for ${DOCKER_PLATFORM} (no provenance/SBOM — Cloud Run compatible)"
for svc in "${SERVICES[@]}"; do
  image="${AR_PREFIX}/${svc}:${IMAGE_TAG}"
  echo "==> Building ${svc}..."
  docker_build_cloudrun "${image}" "${PROJECT_ROOT}/services/${svc}/Dockerfile" "${PROJECT_ROOT}"
  echo "==> Pushing ${image}"
  docker push "${image}"
done

echo "==> Deploying to Cloud Run..."
for svc in "${SERVICES[@]}"; do
  cloud_run_name="${svc//_/-}"
  image="${AR_PREFIX}/${svc}:${IMAGE_TAG}"
  gcloud run deploy "${cloud_run_name}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${image}" \
    --quiet
done

echo ""
echo "Done. Images: ${AR_PREFIX}/*:${IMAGE_TAG}"
