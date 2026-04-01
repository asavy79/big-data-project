"""Firebase UID extraction from the Authorization header.

In production, GCP API Gateway cryptographically verifies the Firebase JWT
before the request reaches this service.  Here we only decode the JWT
payload (without signature verification) to extract the UID — the
expensive verification has already been done upstream.

For local curl testing, the ``X-Firebase-UID`` header is accepted as a
fallback.
"""

import base64
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import async_session

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


def _decode_jwt_payload(token: str) -> dict:
    """Decode a JWT payload without signature verification."""
    payload = token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


async def get_current_uid(request: Request) -> str:
    """Extract the Firebase UID from the request.

    1. Try the Authorization: Bearer <jwt> header (primary path).
    2. Fall back to X-Firebase-UID header (convenient for curl / dev).
    """
    auth_header = request.headers.get("authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            claims = _decode_jwt_payload(token)
            uid = claims.get("user_id") or claims.get("sub")
            if uid:
                return uid
        except Exception as exc:
            logger.warning("JWT payload decode failed: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid token")

    uid = request.headers.get("x-firebase-uid", "").strip()
    if uid:
        return uid

    raise HTTPException(status_code=401, detail="Missing Authorization header")


async def verify_internal(x_internal_key: str = Header(...)):
    """Lightweight guard for service-to-service endpoints."""
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Invalid internal key")
