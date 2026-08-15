"""
Unit tests for auth routes (POST /auth/signup, POST /auth/login)
and the get_current_user dependency.

All DB calls are mocked - no real database connection required.
"""

import os
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import patch

import neo4j.exceptions
import pytest
from fastapi import Depends
from fastapi import FastAPI
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt

from app.auth.router import router as auth_router
from app.dependencies import get_current_user as _get_current_user

if TYPE_CHECKING:
    from collections.abc import Generator

# ---------------------------------------------------------------------------
# Provide required env vars before any app module is imported so that
# pydantic-settings Settings() never reads from the real .env file.
# ---------------------------------------------------------------------------
os.environ["COGNODB_URI"] = "bolt://localhost:7687"
os.environ["COGNODB_USER"] = "test_user"
os.environ["COGNODB_PASSWORD"] = "test_password"  # noqa: S105
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"  # noqa: S105
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_TTL_MINUTES"] = "60"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret-key-for-unit-tests"  # noqa: S105
JWT_ALGORITHM = "HS256"

SIGNUP_URL = "/auth/signup"
LOGIN_URL = "/auth/login"

VALID_SIGNUP = {
    "name": "Alice Example",
    "email": "alice@example.com",
    "password": "strongpassword1",
}

VALID_LOGIN = {
    "email": "alice@example.com",
    "password": "strongpassword1",
}

FAKE_USER_NODE = {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "Alice Example",
    "email": "alice@example.com",
    "password_hash": "placeholder",
    "created_at": "2024-01-01T00:00:00",
}


def _make_test_token(user_id: str, *, expired: bool = False) -> str:
    """Create a JWT signed with the test secret."""
    if expired:
        exp = datetime.now(UTC) - timedelta(minutes=10)
    else:
        exp = datetime.now(UTC) + timedelta(minutes=60)
    payload = {"sub": user_id, "exp": exp}
    return str(jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM))


# ---------------------------------------------------------------------------
# Build a lightweight test application that skips the real lifespan.
# ---------------------------------------------------------------------------


def _build_test_app() -> FastAPI:
    """Return a FastAPI app with auth + test-me routes but NO lifespan."""
    test_app = FastAPI()

    test_app.include_router(auth_router)

    @test_app.get("/test/me")
    async def _me(
        user: dict[str, object] = Depends(_get_current_user),  # noqa: B008
    ) -> dict[str, object]:
        return {"id": user["id"]}

    return test_app


_test_app = _build_test_app()
_TEST_ME_PATH = "/test/me"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> Generator[TestClient]:
    """Synchronous TestClient wrapping the lifespan-free test app."""
    with TestClient(_test_app, raise_server_exceptions=True) as c:
        yield c


# ===========================================================================
# POST /auth/signup
# ===========================================================================


class TestSignup:
    def test_signup_happy_path(self, client: TestClient) -> None:
        """201 + correct JSON body + access_token cookie set."""
        with (
            patch("app.auth.router._pwd_ctx") as mock_ctx,
            patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq,
        ):
            mock_ctx.hash.return_value = "hashed_password"
            mock_rq.side_effect = [
                [],  # GET_USER_BY_EMAIL -> no duplicate
                [{"u": FAKE_USER_NODE}],  # CREATE_USER -> new user
            ]
            resp = client.post(SIGNUP_URL, json=VALID_SIGNUP)

        assert resp.status_code == status.HTTP_201_CREATED, resp.text
        body = resp.json()
        assert body["id"] == FAKE_USER_NODE["id"]
        assert body["name"] == FAKE_USER_NODE["name"]
        assert body["email"] == FAKE_USER_NODE["email"]
        assert "access_token" in resp.cookies

    def test_signup_duplicate_email_returns_409(self, client: TestClient) -> None:
        """409 when email is already registered."""
        with patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq:
            mock_rq.return_value = [{"u": FAKE_USER_NODE}]
            resp = client.post(SIGNUP_URL, json=VALID_SIGNUP)

        assert resp.status_code == status.HTTP_409_CONFLICT, resp.text
        assert "already registered" in resp.json()["detail"]

    def test_signup_invalid_email_returns_422(self, client: TestClient) -> None:
        """422 for a malformed email address."""
        payload = {**VALID_SIGNUP, "email": "not-an-email"}
        resp = client.post(SIGNUP_URL, json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, resp.text

    def test_signup_short_password_returns_422(self, client: TestClient) -> None:
        """422 for a password shorter than 8 characters."""
        payload = {**VALID_SIGNUP, "password": "short"}
        resp = client.post(SIGNUP_URL, json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, resp.text

    def test_signup_empty_name_returns_422(self, client: TestClient) -> None:
        """422 for an empty name."""
        payload = {**VALID_SIGNUP, "name": ""}
        resp = client.post(SIGNUP_URL, json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, resp.text

    def test_signup_missing_fields_returns_422(self, client: TestClient) -> None:
        """422 when the request body is empty."""
        resp = client.post(SIGNUP_URL, json={})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, resp.text

    def test_signup_db_error_on_email_check_returns_503(
        self, client: TestClient
    ) -> None:
        """503 when DB raises ServiceUnavailable during the email check."""

        with patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq:
            mock_rq.side_effect = neo4j.exceptions.ServiceUnavailable("db down")
            resp = client.post(SIGNUP_URL, json=VALID_SIGNUP)

        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, resp.text
        assert "temporarily unavailable" in resp.json()["detail"]

    def test_signup_db_error_on_create_returns_503(self, client: TestClient) -> None:
        """503 when DB raises ServiceUnavailable during user creation."""

        with (
            patch("app.auth.router._pwd_ctx") as mock_ctx,
            patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq,
        ):
            mock_ctx.hash.return_value = "hashed_password"
            mock_rq.side_effect = [
                [],  # email check OK
                neo4j.exceptions.ServiceUnavailable("db down"),  # create fails
            ]
            resp = client.post(SIGNUP_URL, json=VALID_SIGNUP)

        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, resp.text
        assert "temporarily unavailable" in resp.json()["detail"]


# ===========================================================================
# POST /auth/login
# ===========================================================================


class TestLogin:
    def test_login_happy_path(self, client: TestClient) -> None:
        """200 + correct body + access_token cookie set."""
        with (
            patch("app.auth.router._pwd_ctx") as mock_ctx,
            patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq,
        ):
            mock_ctx.verify.return_value = True
            mock_rq.return_value = [{"u": FAKE_USER_NODE}]
            resp = client.post(LOGIN_URL, json=VALID_LOGIN)

        assert resp.status_code == status.HTTP_200_OK, resp.text
        body = resp.json()
        assert body["id"] == FAKE_USER_NODE["id"]
        assert body["email"] == FAKE_USER_NODE["email"]
        assert "access_token" in resp.cookies

    def test_login_wrong_email_returns_401(self, client: TestClient) -> None:
        """401 when no user is found for the given email."""
        with patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq:
            mock_rq.return_value = []
            resp = client.post(LOGIN_URL, json=VALID_LOGIN)

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, resp.text
        assert resp.json()["detail"] == "Invalid credentials."

    def test_login_wrong_password_returns_401(self, client: TestClient) -> None:
        """401 when the password does not match the stored hash."""
        with (
            patch("app.auth.router._pwd_ctx") as mock_ctx,
            patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq,
        ):
            mock_ctx.verify.return_value = False
            mock_rq.return_value = [{"u": FAKE_USER_NODE}]
            resp = client.post(
                LOGIN_URL, json={**VALID_LOGIN, "password": "wrongpassword"}
            )

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, resp.text
        assert resp.json()["detail"] == "Invalid credentials."

    def test_login_db_error_returns_503(self, client: TestClient) -> None:
        """503 when DB raises ServiceUnavailable during login."""

        with patch("app.auth.router.run_query", new_callable=AsyncMock) as mock_rq:
            mock_rq.side_effect = neo4j.exceptions.ServiceUnavailable("db down")
            resp = client.post(LOGIN_URL, json=VALID_LOGIN)

        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, resp.text
        assert "temporarily unavailable" in resp.json()["detail"]

    def test_login_missing_fields_returns_422(self, client: TestClient) -> None:
        """422 when required fields are absent."""
        resp = client.post(LOGIN_URL, json={})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT, resp.text


# ===========================================================================
# GET /test/me - exercises the get_current_user dependency
# ===========================================================================


class TestGetCurrentUser:
    def test_missing_cookie_returns_401(self, client: TestClient) -> None:
        """401 when no access_token cookie is present."""
        resp = client.get(_TEST_ME_PATH)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, resp.text
        assert "Not authenticated" in resp.json()["detail"]

    def test_expired_token_returns_401(self, client: TestClient) -> None:
        """401 when the JWT is expired."""
        token = _make_test_token("some-user-id", expired=True)
        client.cookies.set("access_token", token)
        resp = client.get(_TEST_ME_PATH)
        client.cookies.clear()
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, resp.text
        detail = resp.json()["detail"].lower()
        assert "expired" in detail or "invalid" in detail

    def test_valid_token_unknown_user_returns_401(self, client: TestClient) -> None:
        """401 when JWT is valid but the user no longer exists in the DB."""
        token = _make_test_token("nonexistent-user-id")
        client.cookies.set("access_token", token)
        with patch("app.dependencies.run_query", new_callable=AsyncMock) as mock_rq:
            mock_rq.return_value = []
            resp = client.get(_TEST_ME_PATH)
        client.cookies.clear()

        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, resp.text
        assert "not found" in resp.json()["detail"].lower()

    def test_valid_token_known_user_returns_200(self, client: TestClient) -> None:
        """200 when JWT is valid and the user exists in the DB."""
        user_id = FAKE_USER_NODE["id"]
        token = _make_test_token(user_id)
        client.cookies.set("access_token", token)
        with patch("app.dependencies.run_query", new_callable=AsyncMock) as mock_rq:
            mock_rq.return_value = [{"u": FAKE_USER_NODE}]
            resp = client.get(_TEST_ME_PATH)
        client.cookies.clear()

        assert resp.status_code == status.HTTP_200_OK, resp.text
        assert resp.json()["id"] == user_id
