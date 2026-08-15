import logging
from typing import Any

from fastapi import Cookie
from fastapi import HTTPException
from fastapi import status
from jose import ExpiredSignatureError
from jose import JWTError
from jose import jwt

from app.auth.queries import GET_USER_BY_ID
from app.config import get_settings
from app.database import run_query

logger = logging.getLogger(__name__)


async def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> dict[str, Any]:
    """
    FastAPI dependency that resolves the authenticated user from the
    httpOnly ``access_token`` cookie.

    Raises HTTP 401 for missing, malformed, expired, or revoked tokens.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    cfg = get_settings()

    try:
        payload = jwt.decode(
            access_token,
            cfg.JWT_SECRET,
            algorithms=[cfg.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    rows = await run_query(GET_USER_BY_ID, {"id": user_id})
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    user: dict[str, Any] = rows[0]["u"]
    return user
