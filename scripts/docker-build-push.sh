#!/usr/bin/env bash
# Build the three backend images under services/ (buildx, linux/amd64) and push to Artifact Registry.
#
# Run from anywhere; paths are resolved from the repository root.
#
# Usage:
#   export PROJECT_ID=your-gcp-project-id
#   ./scripts/docker-build-push.sh
#
# Optional:
#   REGION=us-central1 REPOSITORY=service-repo IMAGE_TAG=latest ./scripts/docker-build-push.sh
#
# Cloud Run expects linux/amd64 single-arch manifests (no OCI index from attestations).
#
# On Apple Silicon, --platform linux/amd64 emulates x86; pip in user_service can take 15–40+ minutes
# with little output unless you use plain progress (default below).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"
DOCKER_BUILD_PROGRESS="${DOCKER_BUILD_PROGRESS:-plain}"
REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-service-repo}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

: "${PROJECT_ID:?Set PROJECT_ID (gcloud config get-value project)}"
if [[ "${PROJECT_ID}" == *"@"* ]] || [[ "${PROJECT_ID}" == *"/"* ]]; then
  echo "ERROR: PROJECT_ID must be your GCP project id, not an email or path."
  exit 1
fi

AR_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}"

# name|Dockerfile path relative to PROJECT_ROOT|build context (repo root — Dockerfiles COPY services/<name>/...)
IMAGES=(
  "job_discovery_service|services/job_discovery_service/Dockerfile|."
  "user_service|services/user_service/Dockerfile|."
  "matching_service|services/matching_service/Dockerfile|."
)

echo "==> Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

export BUILDX_NO_DEFAULT_ATTESTATIONS=1

echo "==> Building and pushing (${DOCKER_PLATFORM}) → ${AR_PREFIX}/*:${IMAGE_TAG}"
for spec in "${IMAGES[@]}"; do
  IFS='|' read -r name dockerfile context <<< "${spec}"
  image="${AR_PREFIX}/${name}:${IMAGE_TAG}"
  echo ""
  echo "==> ${name}"
  docker buildx build \
    --progress="${DOCKER_BUILD_PROGRESS}" \
    --platform "${DOCKER_PLATFORM}" \
    --provenance=false \
    --sbom=false \
    -f "${PROJECT_ROOT}/${dockerfile}" \
    -t "${image}" \
    --push \
    "${PROJECT_ROOT}/${context}"
done

echo ""
echo "Done. Images pushed:"
for spec in "${IMAGES[@]}"; do
  IFS='|' read -r name _ _ <<< "${spec}"
  echo "  ${AR_PREFIX}/${name}:${IMAGE_TAG}"
done
