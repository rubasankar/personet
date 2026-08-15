"""
Application entry point.

Startup order:
  1. Configure logging
  2. Connect to Neo4j (via lifespan)
  3. Run schema DDL (idempotent constraints + indexes)
  4. Register routers
"""

import logging
import logging.config
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.config import get_settings
from app.database import close_driver
from app.database import init_driver
from app.database import run_query
from app.network.router import router as network_router
from app.profile.router import router as profile_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# ---------------------------------------------------------------------------
# Logging - configure once at import time so every module's logger works.
# ---------------------------------------------------------------------------

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)-8s %(name)s - %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {"handlers": ["console"], "level": "INFO"},
    }
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema DDL - idempotent; run once on startup.
# ---------------------------------------------------------------------------

_SCHEMA_DDL = [
    # Unique constraints
    (
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
        "FOR (u:User) REQUIRE u.id IS UNIQUE"
    ),
    (
        "CREATE CONSTRAINT user_email_unique IF NOT EXISTS "
        "FOR (u:User) REQUIRE u.email IS UNIQUE"
    ),
    (
        "CREATE CONSTRAINT institution_id_unique IF NOT EXISTS "
        "FOR (i:Institution) REQUIRE i.id IS UNIQUE"
    ),
    (
        "CREATE CONSTRAINT company_id_unique IF NOT EXISTS "
        "FOR (c:Company) REQUIRE c.id IS UNIQUE"
    ),
    # Indexes
    "CREATE INDEX institution_name_index IF NOT EXISTS FOR (i:Institution) ON (i.name)",
    "CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name)",
    "CREATE INDEX user_name_index IF NOT EXISTS FOR (u:User) ON (u.name)",
]


async def _apply_schema() -> None:
    for statement in _SCHEMA_DDL:
        await run_query(statement)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # Always reload settings from the environment / .env file on startup
    # so a server restart picks up any credential or config changes.
    get_settings.cache_clear()
    cfg = get_settings()
    await init_driver(cfg.COGNODB_URI, cfg.COGNODB_USER, cfg.COGNODB_PASSWORD)
    try:
        await _apply_schema()
        logger.info("Schema DDL applied successfully.")
    except Exception as exc:
        logger.critical(
            "Schema initialisation failed - aborting startup: %s", exc, exc_info=True
        )
        sys.exit(1)

    yield

    await close_driver()
    logger.info("Database driver closed.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


_DESCRIPTION = """
PerNet is a **graph-native** REST API for building and exploring professional
and social networks. Relationships between people are stored as graph edges
in a Neo4j database, enabling shortest-path queries and overlap-based
suggestions that a traditional relational database cannot express efficiently.

## Authentication

All endpoints except `POST /auth/signup` and `POST /auth/login` require a
valid session. Authentication is **cookie-based**: a successful signup or
login sets an `httpOnly` cookie named `access_token` containing a signed JWT.
Include that cookie on every subsequent request - no `Authorization` header
is needed.

The cookie is `SameSite=Lax` and `HttpOnly`, so it is not accessible from
JavaScript and is sent automatically by the browser on same-origin requests.

## Typical workflow

```
POST /auth/signup              -> receive access_token cookie
POST /auth/login               -> receive access_token cookie (returning user)

GET  /profile/me               -> read own profile
PATCH /profile/me              -> update name / bio / location
POST /profile/education        -> add an education record
POST /profile/employment       -> add an employment record

GET  /network/users?name=Alice -> find Alice's id
POST /network/connect/{id}     -> connect with Alice
GET  /network/suggestions      -> see who else you might know
GET  /network/path/{id}        -> how are you connected to someone?
GET  /network/search-company/Acme -> who do you know at Acme?
```

## Error conventions

| Status | Meaning |
|--------|---------|
| `400` | Bad request - business-logic validation (e.g. self-connect) |
| `401` | Not authenticated or token expired |
| `404` | Resource not found |
| `409` | Conflict - duplicate resource |
| `422` | Request body / query param validation failed (Pydantic) |
| `503` | Database temporarily unavailable - safe to retry |

Every error response body has the shape `{ "detail": "<message>" }`.
"""

_TAGS_METADATA = [
    {
        "name": "auth",
        "description": (
            "Register and authenticate users. "
            "A successful call sets an `httpOnly` JWT cookie that authorises "
            "all other endpoints."
        ),
    },
    {
        "name": "profile",
        "description": (
            "Manage the authenticated user's profile node and their "
            "`STUDIED_AT` (education) and `WORKED_AT` (employment) graph edges. "
            "All operations are scoped to the currently logged-in user - "
            "there is no admin access to other users' profiles."
        ),
    },
    {
        "name": "network",
        "description": (
            "Explore the social graph. Search for people, create `KNOWS` connections, "
            "find the shortest path between two users, get personalised suggestions, "
            "and discover who you know at a given company."
        ),
    },
]

app = FastAPI(
    title="PerNet - Personal Network Graph API",
    description=_DESCRIPTION,
    version="0.1.0",
    contact={
        "name": "PerNet team",
    },
    license_info={
        "name": "Private",
    },
    openapi_tags=_TAGS_METADATA,
    lifespan=lifespan,
    redoc_url="/redoc",
    docs_url="/docs",
)

_cfg = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cfg.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers define their own prefix - do NOT add a second prefix here.
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(network_router)
