"""Lightweight API gateway that validates Firebase ID tokens and proxies
requests to the appropriate backend service.

In production this role would be filled by GCP API Gateway or similar.
For local development it runs as a Docker container alongside the other services.

DEV_MODE=true decodes the Firebase JWT payload without cryptographic
verification (no GCP credentials needed).  It also accepts the raw
``X-Firebase-UID`` header so you can curl the API without a real token.
"""

import base64
import json
import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEV_MODE = os.environ.get("DEV_MODE", "").lower() in ("true", "1", "yes")

USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://user-service:8000")
JOB_SERVICE_URL = os.environ.get("JOB_SERVICE_URL", "http://job-discovery-service:8000")

FIREBASE_PROJECT_ID = os.environ.get(
    "FIREBASE_PROJECT_ID",
    os.environ.get("GCP_PROJECT_ID", "local-project"),
)

if not DEV_MODE:
    import firebase_admin
    from firebase_admin import auth as firebase_auth

    firebase_admin.initialize_app(options={"projectId": FIREBASE_PROJECT_ID})

app = FastAPI(title="API Gateway")
http_client = httpx.AsyncClient(timeout=30.0)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------
def _decode_jwt_payload(token: str) -> dict:
    """Decode a JWT payload WITHOUT signature verification (DEV_MODE only)."""
    payload = token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


async def _extract_uid(request: Request) -> str:
    """Return a Firebase UID from the request.

    Production: full cryptographic verification via Firebase Admin SDK.
    DEV_MODE: decodes the JWT payload to read the UID (trusts the token).
    Also accepts raw ``X-Firebase-UID`` header in DEV_MODE for curl testing.
    """
    auth_header = request.headers.get("authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")

        if DEV_MODE:
            try:
                claims = _decode_jwt_payload(token)
                uid = claims.get("user_id") or claims.get("sub")
                if uid:
                    return uid
            except Exception as exc:
                logger.warning("JWT decode failed: %s", exc)
        else:
            try:
                decoded = firebase_auth.verify_id_token(token)
                return decoded["uid"]
            except Exception as exc:
                logger.warning("Token verification failed: %s", exc)
                raise HTTPException(status_code=401, detail="Invalid or expired token")

    if DEV_MODE:
        uid = request.headers.get("x-firebase-uid", "").strip()
        if uid:
            return uid

    raise HTTPException(status_code=401, detail="Missing Authorization header")


# ---------------------------------------------------------------------------
# Reverse proxy helper
# ---------------------------------------------------------------------------
HOP_BY_HOP = frozenset(("host", "connection", "transfer-encoding", "keep-alive"))


async def _proxy(
    request: Request,
    target_url: str,
    extra_headers: dict[str, str] | None = None,
) -> Response:
    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP
    }
    if extra_headers:
        headers.update(extra_headers)

    body = await request.body()

    upstream = await http_client.request(
        method=request.method,
        url=target_url,
        headers=headers,
        content=body,
        params=dict(request.query_params),
    )

    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.api_route(
    "/api/user/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_user(request: Request, path: str):
    uid = await _extract_uid(request)
    target = f"{USER_SERVICE_URL}/{path}"
    return await _proxy(request, target, extra_headers={"X-Firebase-UID": uid})


@app.api_route(
    "/api/jobs/{path:path}",
    methods=["GET", "POST"],
)
async def proxy_jobs(request: Request, path: str):
    target = f"{JOB_SERVICE_URL}/{path}"
    return await _proxy(request, target)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}
