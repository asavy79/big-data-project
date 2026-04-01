#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# deploy.sh — Build, push, and deploy the JobMatch platform
#
# Usage:
#   ./deploy.sh                  # deploy everything
#   ./deploy.sh --services-only  # skip frontend, only build & push Cloud Run images
#   ./deploy.sh --frontend-only  # skip services, only build & upload frontend
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Read variables from Terraform output (requires prior `terraform apply`)
cd "$SCRIPT_DIR"
PROJECT_ID=$(terraform output -raw 2>/dev/null <<< '' || true)

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: Set PROJECT_ID environment variable or run terraform apply first"
    echo "  export PROJECT_ID=your-gcp-project-id"
    exit 1
fi

: "${PROJECT_ID:?Set PROJECT_ID}"
: "${REGION:=us-central1}"

AR_REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/jobmatch"
SERVICES=("job_discovery_service" "user_service" "matching_service")

DEPLOY_SERVICES=true
DEPLOY_FRONTEND=true

for arg in "$@"; do
    case "$arg" in
        --services-only) DEPLOY_FRONTEND=false ;;
        --frontend-only) DEPLOY_SERVICES=false ;;
    esac
done

# ---------------------------------------------------------------------------
# 1. Authenticate Docker to Artifact Registry
# ---------------------------------------------------------------------------
echo "==> Configuring Docker for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ---------------------------------------------------------------------------
# 2. Build & push service images
# ---------------------------------------------------------------------------
if [ "$DEPLOY_SERVICES" = true ]; then
    IMAGE_TAG="${IMAGE_TAG:-latest}"
    for svc in "${SERVICES[@]}"; do
        echo "==> Building ${svc}..."
        docker build \
            -t "${AR_REPO}/${svc}:${IMAGE_TAG}" \
            "${PROJECT_ROOT}/services/${svc}/"

        echo "==> Pushing ${svc}..."
        docker push "${AR_REPO}/${svc}:${IMAGE_TAG}"
    done

    echo "==> Updating Cloud Run services..."
    for svc in "${SERVICES[@]}"; do
        cloud_run_name="${svc//_/-}"
        gcloud run services update "$cloud_run_name" \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --image="${AR_REPO}/${svc}:${IMAGE_TAG}" \
            --quiet
    done
fi

# ---------------------------------------------------------------------------
# 3. Build & upload frontend
# ---------------------------------------------------------------------------
if [ "$DEPLOY_FRONTEND" = true ]; then
    BUCKET_NAME=$(cd "$SCRIPT_DIR" && terraform output -raw frontend_bucket 2>/dev/null || echo "")
    if [ -z "$BUCKET_NAME" ]; then
        echo "ERROR: Could not read frontend_bucket from terraform output."
        echo "  Run: cd infrastructure && terraform output frontend_bucket"
        exit 1
    fi

    echo "==> Building frontend..."
    cd "${PROJECT_ROOT}/frontend"
    npm ci
    npm run build

    echo "==> Uploading to gs://${BUCKET_NAME}/..."
    gcloud storage cp -r dist/* "gs://${BUCKET_NAME}/"

    echo "==> Invalidating CDN cache..."
    gcloud compute url-maps invalidate-cdn-cache jobmatch-url-map \
        --path="/*" \
        --project="$PROJECT_ID" \
        --quiet || true
fi

echo ""
echo "==> Deploy complete!"
if [ "$DEPLOY_SERVICES" = true ]; then
    echo "    Services pushed to: ${AR_REPO}/*:${IMAGE_TAG:-latest}"
fi
if [ "$DEPLOY_FRONTEND" = true ]; then
    echo "    Frontend uploaded to: gs://${BUCKET_NAME:-<bucket>}/"
fi

LB_IP=$(cd "$SCRIPT_DIR" && terraform output -raw load_balancer_ip 2>/dev/null || echo "<pending>")
echo "    Load balancer IP: http://${LB_IP}"
