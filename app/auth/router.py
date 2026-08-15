"""
Auth router:
  POST /auth/signup  - register a new user
  POST /auth/login   - authenticate an existing user
"""

import logging
import uuid
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import bcrypt
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from jose import jwt

from app.auth.queries import CREATE_USER
from app.auth.queries import GET_USER_BY_EMAIL
from app.auth.schemas import LoginRequest
from app.auth.schemas import SignupRequest
from app.auth.schemas import TokenResponse
from app.config import Settings
from app.config import get_settings
from app.database import handle_db_errors
from app.database import run_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID = "Invalid credentials."

# ---------------------------------------------------------------------------
# Password helpers - wrapping bcrypt directly to avoid the passlib/bcrypt
# 72-byte probe incompatibility introduced in bcrypt 4.x.
# ---------------------------------------------------------------------------


class _PwdCtx:
    """Thin bcrypt wrapper that mirrors the passlib .hash() / .verify() API."""

    @staticmethod
    def hash(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except ValueError:
            return False


_pwd_ctx = _PwdCtx()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_token(user_id: str, cfg: Settings) -> str:
    """Return a signed JWT with ``sub=user_id`` and ``exp=now+TTL``."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + timedelta(minutes=cfg.JWT_TTL_MINUTES),
    }
    return str(jwt.encode(payload, cfg.JWT_SECRET, algorithm=cfg.JWT_ALGORITHM))


def _set_auth_cookie(response: Response, token: str, cfg: Settings) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=cfg.is_production,  # True behind HTTPS in production
    )


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
    summary="Register a new user",
    responses={
        409: {"description": "Email already registered"},
        503: {"description": "Database temporarily unavailable"},
    },
)
@handle_db_errors("signup")
async def signup(body: SignupRequest, response: Response) -> TokenResponse:
    """
    Create a new account and immediately authenticate the user.

    On success the response sets an `httpOnly` cookie named `access_token`
    containing a signed JWT. Pass that cookie on all subsequent requests -
    no extra step is needed.

    **Duplicate emails** return `409`. The email is stored in lower-case so
    `Alice@Example.com` and `alice@example.com` are treated as the same address.
    """
    cfg = get_settings()

    # 1. Reject duplicate emails.
    existing = await run_query(GET_USER_BY_EMAIL, {"email": body.email})

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email is already registered.",
        )

    # 2. Hash password, generate UUID, persist user.
    password_hash = _pwd_ctx.hash(body.password)
    user_id = str(uuid.uuid4())

    rows = await run_query(
        CREATE_USER,
        {
            "id": user_id,
            "name": body.name,
            "email": body.email,
            "password_hash": password_hash,
        },
    )

    user = rows[0]["u"]

    # 3. Issue JWT and set httpOnly cookie.
    token = _make_token(user["id"], cfg)
    _set_auth_cookie(response, token, cfg)

    logger.info("User %s signed up successfully.", user["id"])
    return TokenResponse(id=user["id"], name=user["name"], email=user["email"])


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Authenticate an existing user",
    responses={
        401: {"description": "Invalid credentials"},
        503: {"description": "Database temporarily unavailable"},
    },
)
@handle_db_errors("login")
async def login(body: LoginRequest, response: Response) -> TokenResponse:
    """
    Authenticate with email and password.

    On success the response sets an `httpOnly` cookie named `access_token`.
    The same `401` message is returned for both an unknown email and a wrong
    password to prevent user-enumeration attacks.
    """
    cfg = get_settings()

    # 1. Look up the user by email.
    rows = await run_query(GET_USER_BY_EMAIL, {"email": body.email})

    # 2. Verify credentials - same 401 message for unknown email OR wrong password
    #    to prevent user-enumeration attacks.
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID)

    user = rows[0]["u"]

    if not _pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID)

    # 3. Issue JWT and set httpOnly cookie.
    token = _make_token(user["id"], cfg)
    _set_auth_cookie(response, token, cfg)

    logger.info("User %s logged in successfully.", user["id"])
    return TokenResponse(id=user["id"], name=user["name"], email=user["email"])
