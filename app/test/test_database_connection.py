"""
Smoke test: verify the database driver can connect using settings from the
environment / .env file.

Run only when a real database is available (e.g., in CI with the service
container running). Skip this test locally if no database is reachable.
"""

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from app.config import get_settings
from app.database import close_driver
from app.database import init_driver
from app.database import run_query

# ---------------------------------------------------------------------------
# Load .env values directly so test_auth.py's os.environ overrides don't
# interfere. We resolve the .env file relative to the project root (two
# directories above this file: app/test/ -> app/ -> project root).
# ---------------------------------------------------------------------------
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"
_ENV_VALUES: dict[str, str] = {
    k: v for k, v in dotenv_values(_ENV_FILE).items() if v is not None
}


@pytest.mark.asyncio
async def test_database_connectivity() -> None:
    """Assert that a query round-trip succeeds with the configured driver."""
    # Temporarily restore real env values, clearing the settings cache so
    # pydantic-settings re-reads them rather than using the fake values set
    # by test_auth at import time.
    original = {k: os.environ.get(k) for k in _ENV_VALUES}
    os.environ.update(_ENV_VALUES)
    get_settings.cache_clear()
    try:
        cfg = get_settings()
        await init_driver(cfg.COGNODB_URI, cfg.COGNODB_USER, cfg.COGNODB_PASSWORD)
        try:
            result = await run_query("RETURN 1 AS n")
            assert result == [{"n": 1}]
        finally:
            await close_driver()
    finally:
        # Restore whatever was there before (fake values or nothing).
        for k, v in original.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        get_settings.cache_clear()
