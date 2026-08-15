"""
Network router:
  GET  /network/users                              - search people by name + optional filters
  POST /network/connect/{target_user_id}           - create bidirectional KNOWS (by id)
  DELETE /network/connect/{target_user_id}         - remove a connection
  PATCH /network/connect/{target_user_id}          - update a connection
  GET  /network/connections                        - list all direct connections
  GET  /network/suggestions                        - overlap-score suggestions
  GET  /network/intro/{target_user_id}             - best route to reach someone

Typical workflow:
  1. GET /network/users?name=Alice&company=Acme   - find the right person
  2. GET /network/intro/{id}                      - see how to reach them
  3. POST /network/connect/{id}                   - connect using the id from step 1
"""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from fastapi import status

from app.database import handle_db_errors
from app.database import run_query
from app.dependencies import get_current_user
from app.network.queries import CREATE_KNOWS_PAIR
from app.network.queries import FIND_CLOSE_PATH
from app.network.queries import FIND_INTRO_VIA_KNOWS
from app.network.queries import FIND_INTRO_VIA_MY_CONTEXT
from app.network.queries import FIND_SHARED_CONTEXT
from app.network.queries import FIND_SHORTEST_PATH
from app.network.queries import FIND_USER_BY_ID
from app.network.queries import GET_CONNECTIONS
from app.network.queries import GET_SUGGESTIONS
from app.network.queries import REMOVE_KNOWS_PAIR
from app.network.queries import SEARCH_USERS
from app.network.queries import UPDATE_KNOWS_PAIR
from app.network.schemas import ConnectionItem
from app.network.schemas import ConnectRequest
from app.network.schemas import IntroResponse
from app.network.schemas import IntroSuggestion
from app.network.schemas import IntroType
from app.network.schemas import PathNode
from app.network.schemas import SuggestionItem
from app.network.schemas import UpdateConnectionRequest
from app.network.schemas import UserSearchItem
from app.schemas.common import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/network", tags=["network"])

_404 = {"description": "Resource not found"}
_503 = {"description": "Database temporarily unavailable"}


# ---------------------------------------------------------------------------
# GET /network/users
# ---------------------------------------------------------------------------


@router.get(
    "/users",
    response_model=list[UserSearchItem],
    summary="Search for people",
    responses={503: _503},
)
@handle_db_errors("search_users")
async def search_users(
    name: str = Query(
        min_length=1,
        description="Partial, case-insensitive name match. `ali` matches Alice, Malik, Talia, etc.",
        examples=["alice"],
    ),
    location: str | None = Query(
        default=None,
        description='Narrow by location (partial, case-insensitive). E.g. `london` matches "London, UK".',
        examples=["london"],
    ),
    company: str | None = Query(
        default=None,
        description="Narrow to people with a `WORKED_AT` edge to a company whose name contains this string.",
        examples=["acme"],
    ),
    institution: str | None = Query(
        default=None,
        description="Narrow to people with a `STUDIED_AT` edge to an institution whose name contains this string.",
        examples=["cape town"],
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results. Min 1, max 100, default 20.",
        examples=[20],
    ),
    current_user: dict = Depends(get_current_user),
) -> list[UserSearchItem]:
    """
    Search the user graph by name with optional narrowing filters.

    All text comparisons are **partial and case-insensitive** (`CONTAINS`):
    - `name=ali` -> matches Alice, Malik, Natalia, ...
    - `company=acme` -> matches "Acme Corp", "Acme Ltd", ...
    - `location=london` -> matches "London, UK", "East London", ...

    All supplied filters are combined with **AND** - every filter must match.
    Omit a filter to ignore that dimension entirely.

    The `id` in each result is what you pass to
    `POST /network/connect/{target_user_id}` or
    `GET /network/path/{target_user_id}`.

    **Examples**

    Find everyone named Alice:
    ```
    GET /network/users?name=alice
    ```
    Find Alice who works at Acme in London:
    ```
    GET /network/users?name=alice&company=acme&location=london
    ```
    """
    rows = await run_query(
        SEARCH_USERS,
        {
            "my_id": current_user["id"],
            "name": name,
            "location": location,
            "company": company,
            "institution": institution,
            "limit": limit,
        },
    )

    return [
        UserSearchItem(
            id=row["id"],
            name=row["name"],
            location=row.get("location"),
            companies=row["companies"] or [],
            institutions=row["institutions"] or [],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# POST /network/connect/{target_user_id}
# ---------------------------------------------------------------------------


@router.post(
    "/connect/{target_user_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    summary="Connect with a user",
    responses={
        400: {"description": "Self-connect attempt"},
        404: _404,
        503: _503,
    },
)
@handle_db_errors("connect")
async def connect(
    target_user_id: UUID = Path(
        description="UUID of the user to connect with. Obtain this from `GET /network/users`.",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    ),
    body: ConnectRequest = ...,
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """
    Create a **bidirectional** `KNOWS` relationship between the authenticated
    user and `target_user_id`.

    The relationship is created in both directions (`a->b` and `b->a`) so that
    graph traversal queries work regardless of direction. The underlying Cypher
    uses `MERGE`, so calling this endpoint twice for the same pair is safe -
    it will not create duplicate edges.

    **Finding the target's id**

    If you only know the person's name, use `GET /network/users` first:
    ```
    GET /network/users?name=alice&company=acme
    -> [{ "id": "b2c3d4e5-...", "name": "Alice Mbeki", ... }]

    POST /network/connect/b2c3d4e5-...
    { "context": "colleague", "closeness": "acquaintance" }
    ```
    """
    my_id: str = current_user["id"]
    target_id: str = str(target_user_id)

    if my_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot connect with yourself.",
        )

    target_rows = await run_query(FIND_USER_BY_ID, {"id": target_id})
    if not target_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    since_value = body.since.isoformat() if body.since is not None else None

    await run_query(
        CREATE_KNOWS_PAIR,
        {
            "user_id": my_id,
            "target_id": target_id,
            "context": body.context.value,
            "since": since_value,
            "closeness": body.closeness.value,
        },
    )

    logger.info(
        "User %s connected with user %s (%s).", my_id, target_id, target_rows[0]["name"]
    )
    return MessageResponse(detail="Connection created.")


# ---------------------------------------------------------------------------
# GET /network/connections
# ---------------------------------------------------------------------------


@router.get(
    "/connections",
    response_model=list[ConnectionItem],
    summary="List your connections",
    responses={503: _503},
)
@handle_db_errors("get_connections")
async def get_connections(
    current_user: dict = Depends(get_current_user),
) -> list[ConnectionItem]:
    """
    Return all users you are directly connected to via `KNOWS`, ordered
    alphabetically by name.

    Returns an empty list if you have no connections yet.
    """
    rows = await run_query(GET_CONNECTIONS, {"my_id": current_user["id"]})
    return [
        ConnectionItem(
            id=row["id"],
            name=row["name"],
            location=row.get("location"),
            context=row["context"],
            since=row.get("since"),
            closeness=row["closeness"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# DELETE /network/connect/{target_user_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/connect/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a connection",
    responses={
        400: {"description": "Self-disconnect attempt"},
        404: _404,
        503: _503,
    },
)
@handle_db_errors("disconnect")
async def disconnect(
    target_user_id: UUID = Path(
        description="UUID of the user to disconnect from.",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    ),
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Remove the `KNOWS` relationship between you and `target_user_id` in both
    directions.

    Returns `404` if no connection exists between the two users.
    """
    my_id: str = current_user["id"]
    target_id: str = str(target_user_id)

    if my_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot disconnect from yourself.",
        )

    rows = await run_query(REMOVE_KNOWS_PAIR, {"my_id": my_id, "target_id": target_id})

    if not rows or rows[0]["deleted"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connection found between these users.",
        )

    logger.info("User %s disconnected from user %s.", my_id, target_id)


# ---------------------------------------------------------------------------
# PATCH /network/connect/{target_user_id}
# ---------------------------------------------------------------------------


@router.patch(
    "/connect/{target_user_id}",
    response_model=ConnectionItem,
    summary="Update a connection",
    responses={
        400: {"description": "Self-update attempt"},
        404: _404,
        503: _503,
    },
)
@handle_db_errors("update_connection")
async def update_connection(
    target_user_id: UUID = Path(
        description="UUID of the connected user to update.",
        examples=["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
    ),
    body: UpdateConnectionRequest = ...,
    current_user: dict = Depends(get_current_user),
) -> ConnectionItem:
    """
    Update `context`, `since`, and/or `closeness` on an existing `KNOWS`
    relationship. All fields are optional - only the ones you include are
    changed.

    Both directions of the relationship are updated atomically so the graph
    stays consistent.

    Common use case - marking an acquaintance as a close connection over time:
    ```json
    { "closeness": "close" }
    ```

    Returns `404` if no connection exists between the two users.
    """
    my_id: str = current_user["id"]
    target_id: str = str(target_user_id)

    if my_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot update a connection with yourself.",
        )

    since_value = body.since.isoformat() if body.since is not None else None

    rows = await run_query(
        UPDATE_KNOWS_PAIR,
        {
            "my_id": my_id,
            "target_id": target_id,
            "context": body.context.value if body.context else None,
            "since": since_value,
            "closeness": body.closeness.value if body.closeness else None,
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connection found between these users.",
        )

    # Fetch the target user's profile details for the response.
    target_rows = await run_query(FIND_USER_BY_ID, {"id": target_id})
    target = target_rows[0] if target_rows else {"name": "", "location": None}

    logger.info(
        "User %s updated connection with user %s (closeness=%s).",
        my_id,
        target_id,
        rows[0]["closeness"],
    )
    return ConnectionItem(
        id=target_id,
        name=target.get("name", ""),
        location=target.get("location"),
        context=rows[0]["context"],
        since=rows[0].get("since"),
        closeness=rows[0]["closeness"],
    )


# ---------------------------------------------------------------------------
# GET /network/suggestions
# ---------------------------------------------------------------------------


@router.get(
    "/suggestions",
    response_model=list[SuggestionItem],
    summary="Get connection suggestions",
    responses={503: _503},
)
@handle_db_errors("suggestions")
async def suggestions(
    current_user: dict = Depends(get_current_user),
) -> list[SuggestionItem]:
    """
    Return up to **10** people you might know, ranked by `overlap_score`.

    A suggestion is any user who:
    - shares at least one Institution or Company with you (`STUDIED_AT` or
      `WORKED_AT` edges to the same node), **and**
    - is not already connected to you via a `KNOWS` edge.

    `overlap_score` is the count of shared nodes - higher means more things
    in common. `shared_context` lists the names of those shared nodes so you
    can display "You both worked at Acme Corp" on the suggestion card.

    Returns an **empty list** when you have no shared context with anyone -
    not a `404`. Render this as an empty state ("No suggestions yet").
    """
    rows = await run_query(GET_SUGGESTIONS, {"my_id": current_user["id"]})

    return [
        SuggestionItem(
            id=row["id"],
            name=row["name"],
            location=row.get("location"),
            shared_context=row["shared_context"],
            overlap_score=row["overlap_score"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# GET /network/intro/{target_user_id}
# ---------------------------------------------------------------------------


@router.get(
    "/intro/{target_user_id}",
    response_model=IntroResponse,
    summary="Find the best way to reach someone",
    responses={
        400: {"description": "Target is self"},
        404: {"description": "Target user does not exist"},
        503: _503,
    },
)
@handle_db_errors("intro")
async def find_intro(
    target_user_id: UUID = Path(
        description="UUID of the person you want to reach.",
        examples=["c3d4e5f6-a7b8-9012-cdef-123456789012"],
    ),
    current_user: dict = Depends(get_current_user),
) -> IntroResponse:
    """
    Find the **best route** to reach `target_user_id`, in order of preference:

    1. **direct_context** - you share a company or institution with the target.
       You already have common ground to reach out directly.

    2. **knows_path** - a `KNOWS` chain of ≤ 7 hops exists. Returns the full
       chain. Prefers all-`close` paths when available (`via_close_only: true`).

    3. **suggested_intro** - no `KNOWS` path, but there are people you know
       (within 3 hops) who share a company/institution with the target.
       Connect with them first to get a warm introduction.

    4. **unreachable** - none of the above apply.
    """
    my_id: str = current_user["id"]
    target_id: str = str(target_user_id)

    if my_id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot find a path to yourself.",
        )

    # Confirm target exists
    target_rows = await run_query(FIND_USER_BY_ID, {"id": target_id})
    if not target_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )

    # ── Run all stages concurrently ───────────────────────────────────────
    shared_task = run_query(
        FIND_SHARED_CONTEXT, {"my_id": my_id, "target_id": target_id}
    )
    close_task = run_query(FIND_CLOSE_PATH, {"my_id": my_id, "target_id": target_id})
    path_task = run_query(FIND_SHORTEST_PATH, {"my_id": my_id, "target_id": target_id})
    intro_knows_task = run_query(
        FIND_INTRO_VIA_KNOWS, {"my_id": my_id, "target_id": target_id}
    )
    intro_context_task = run_query(
        FIND_INTRO_VIA_MY_CONTEXT, {"my_id": my_id, "target_id": target_id}
    )

    (
        shared_rows,
        close_rows,
        path_rows,
        intro_knows_rows,
        intro_context_rows,
    ) = await asyncio.gather(
        shared_task, close_task, path_task, intro_knows_task, intro_context_task
    )

    shared_context = [row["name"] for row in shared_rows]
    via_close_only = bool(close_rows)
    best_path_rows = close_rows or path_rows

    # Merge and deduplicate intro candidates; prefer knows-based bridges first
    seen_ids: set[str] = set()
    intro_rows: list[dict] = []
    for row in list(intro_knows_rows) + list(intro_context_rows):
        if row["intro_id"] not in seen_ids:
            seen_ids.add(row["intro_id"])
            intro_rows.append(row)
    intro_rows = intro_rows[:3]

    def _build_suggestion(row: dict) -> IntroSuggestion:
        raw_chain = row.get("chain_to_target") or []
        return IntroSuggestion(
            id=row["intro_id"],
            name=row["intro_name"],
            location=row.get("intro_location"),
            knows_distance=row["knows_distance"],
            shared_node_name=row["shared_node_name"],
            shared_node_type=row["shared_node_type"],
            reach_type=row["reach_type"],
            chain_to_target=[PathNode(id=n["id"], name=n["name"]) for n in raw_chain],
        )

    # ── Determine primary type ────────────────────────────────────────────
    if best_path_rows:
        chain = [
            PathNode(id=n["id"], name=n["name"]) for n in best_path_rows[0]["chain"]
        ]
        return IntroResponse(
            type=IntroType.knows_path,
            shared_context=shared_context,
            chain=chain,
            hops=best_path_rows[0]["hops"],
            via_close_only=via_close_only,
        )

    if shared_context:
        return IntroResponse(
            type=IntroType.direct_context,
            shared_context=shared_context,
            suggestions=[_build_suggestion(r) for r in intro_rows],
        )

    if intro_rows:
        return IntroResponse(
            type=IntroType.suggested_intro,
            suggestions=[_build_suggestion(r) for r in intro_rows],
        )

    return IntroResponse(type=IntroType.unreachable)
