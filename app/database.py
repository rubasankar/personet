import logging
from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import TypeVar

import neo4j.exceptions
from fastapi import HTTPException
from fastapi import status
from neo4j import AsyncDriver
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

_DB_UNAVAILABLE = "Database is temporarily unavailable. Please try again later."


_F = TypeVar("_F", bound=Callable[..., Any])


def handle_db_errors(context: str) -> Callable[[_F], _F]:
    """
    Decorator for route handlers: converts Neo4j connectivity/auth errors
    into a 503 Service Unavailable response.

    Usage::

        @router.get("/something")
        @handle_db_errors("my_handler")
        async def my_handler(...):
            ...
    """

    def decorator(fn: _F) -> _F:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await fn(*args, **kwargs)
            except (
                neo4j.exceptions.ServiceUnavailable,
                neo4j.exceptions.AuthError,
            ) as exc:
                logger.error("DB error during %s: %s", context, exc, exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=_DB_UNAVAILABLE,
                )

        return wrapper  # type: ignore[return-value]

    return decorator


_driver: AsyncDriver | None = None


async def init_driver(uri: str, user: str, password: str) -> None:
    global _driver
    _driver = AsyncGraphDatabase.driver(uri, auth=(user, password))


async def close_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def run_query(
    cypher: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    if _driver is None:
        msg = (
            "Database driver has not been initialised. "
            "Ensure init_driver() is called during application startup."
        )
        raise RuntimeError(msg)
    async with _driver.session() as session:
        result = await session.run(cypher, params or {})
        return [record.data() async for record in result]
