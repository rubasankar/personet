"""
Profile router - full CRUD

User profile:
  GET    /profile/me                                        - read own profile
  PATCH  /profile/me                                        - update name / bio / location
  DELETE /profile/me                                        - delete account + all relationships

Education (STUDIED_AT):
  POST   /profile/education                                 - add record
  GET    /profile/education                                 - list all records
  PATCH  /profile/education/{institution_name}/{start_year} - update a record
  DELETE /profile/education/{institution_name}/{start_year} - remove a record

Employment (WORKED_AT):
  POST   /profile/employment                                - add record
  GET    /profile/employment                                - list all records
  PATCH  /profile/employment/{company_name}/{start_year}    - update a record
  DELETE /profile/employment/{company_name}/{start_year}    - remove a record
"""

import logging
from urllib.parse import unquote

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import status

from app.database import handle_db_errors
from app.database import run_query
from app.dependencies import get_current_user
from app.profile.queries import CREATE_STUDIED_AT
from app.profile.queries import CREATE_WORKED_AT
from app.profile.queries import DELETE_PROFILE
from app.profile.queries import DELETE_STUDIED_AT
from app.profile.queries import DELETE_WORKED_AT
from app.profile.queries import GET_EDUCATION
from app.profile.queries import GET_EMPLOYMENT
from app.profile.queries import GET_PROFILE_ME
from app.profile.queries import MERGE_COMPANY
from app.profile.queries import MERGE_INSTITUTION
from app.profile.queries import UPDATE_PROFILE
from app.profile.queries import UPDATE_STUDIED_AT
from app.profile.queries import UPDATE_WORKED_AT
from app.profile.schemas import EducationItem
from app.profile.schemas import EducationRequest
from app.profile.schemas import EducationUpdateRequest
from app.profile.schemas import EmploymentItem
from app.profile.schemas import EmploymentRequest
from app.profile.schemas import EmploymentUpdateRequest
from app.profile.schemas import ProfileResponse
from app.profile.schemas import ProfileUpdateRequest
from app.schemas.common import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])

_404 = {"description": "Resource not found"}
_503 = {"description": "Database temporarily unavailable"}
_422 = {"description": "Request validation failed"}


# ===========================================================================
# User profile
# ===========================================================================


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Get own profile",
    responses={404: _404, 503: _503},
)
@handle_db_errors("get_profile_me")
async def get_profile_me(
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    """
    Return the authenticated user's profile node plus their total direct
    connection count (`connection_count` = number of outgoing `KNOWS` edges).

    Use this on the dashboard and profile page to render the current user's
    card. The `id` returned here is the UUID you need for network endpoints.
    """
    rows = await run_query(GET_PROFILE_ME, {"id": current_user["id"]})

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    row = rows[0]
    user = row["u"]
    return ProfileResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        bio=user.get("bio"),
        location=user.get("location"),
        connection_count=row["connection_count"],
    )


@router.patch(
    "/me",
    response_model=ProfileResponse,
    summary="Update own profile",
    responses={422: _422, 503: _503},
)
@handle_db_errors("update_profile_me")
async def update_profile_me(
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    """
    Partially update `name`, `bio`, and/or `location`.

    This is a **PATCH** - only the fields present in the request body are
    written. Omit a field entirely to leave it unchanged. Sending `null`
    explicitly for a field is not supported; use omission instead.

    The `email` and `id` fields are immutable and cannot be changed here.
    """
    rows = await run_query(
        UPDATE_PROFILE,
        {
            "id": current_user["id"],
            "name": body.name,
            "bio": body.bio,
            "location": body.location,
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    row = rows[0]
    user = row["u"]
    logger.info("User %s updated their profile.", current_user["id"])
    return ProfileResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        bio=user.get("bio"),
        location=user.get("location"),
        connection_count=row["connection_count"],
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own account",
    responses={503: _503},
)
@handle_db_errors("delete_profile_me")
async def delete_profile_me(
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Permanently delete the authenticated user's account.

    This runs a `DETACH DELETE` on the User node, which removes the node
    **and all relationships** attached to it - `KNOWS`, `STUDIED_AT`,
    `WORKED_AT`. The action is **irreversible**.

    After this call the `access_token` cookie is no longer valid; redirect
    the user to the login page.
    """
    await run_query(DELETE_PROFILE, {"id": current_user["id"]})
    logger.info("User %s deleted their account.", current_user["id"])


# ===========================================================================
# Education
# ===========================================================================


@router.post(
    "/education",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    summary="Add an education record",
    responses={422: _422, 503: _503},
)
@handle_db_errors("add_education")
async def add_education(
    body: EducationRequest,
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """
    Attach a `STUDIED_AT` edge between the current user and an Institution
    node, creating the Institution if it does not already exist (`MERGE`).

    The composite key for a record is **`institution_name` + `start_year`**.
    Use this pair to target the record in `PATCH` and `DELETE` calls.

    Multiple records at the same institution are allowed as long as they
    have different `start_year` values (e.g. a second degree).
    """
    await run_query(
        MERGE_INSTITUTION,
        {"name": body.institution_name, "type": body.institution_type.value},
    )
    await run_query(
        CREATE_STUDIED_AT,
        {
            "user_id": current_user["id"],
            "institution_name": body.institution_name,
            "degree": body.degree,
            "department": body.department,
            "start_year": body.start_year,
            "end_year": body.end_year,
        },
    )
    logger.info(
        "User %s added education at %s.", current_user["id"], body.institution_name
    )
    return MessageResponse(detail="Education record created.")


@router.get(
    "/education",
    response_model=list[EducationItem],
    summary="List education records",
    responses={503: _503},
)
@handle_db_errors("get_education")
async def get_education(
    current_user: dict = Depends(get_current_user),
) -> list[EducationItem]:
    """
    Return all education records for the authenticated user, ordered by
    `start_year` descending (most recent first).

    Returns an empty list if no records have been added yet - not a `404`.
    """
    rows = await run_query(GET_EDUCATION, {"user_id": current_user["id"]})
    return [
        EducationItem(
            institution_name=row["institution_name"],
            institution_type=row["institution_type"],
            degree=row["degree"],
            department=row["department"],
            start_year=row["start_year"],
            end_year=row["end_year"],
        )
        for row in rows
    ]


@router.patch(
    "/education/{institution_name}/{start_year}",
    response_model=EducationItem,
    summary="Update an education record",
    responses={404: _404, 422: _422, 503: _503},
)
@handle_db_errors("update_education")
async def update_education(
    institution_name: str = Path(
        description="Exact institution name as stored (URL-encoded if it contains spaces).",
        examples=["University of Cape Town"],
    ),
    start_year: int = Path(
        description="The `start_year` of the record to update.",
        examples=[2018],
    ),
    body: EducationUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
) -> EducationItem:
    """
    Partially update one education record identified by its composite key
    **`institution_name` + `start_year`**.

    Only the fields present in the body are changed; omit a field to leave
    it as-is. `institution_name` and `start_year` are immutable keys -
    to correct them, delete the record and re-add it.

    **Path encoding**: if the institution name contains spaces or special
    characters, URL-encode it - e.g. `University%20of%20Cape%20Town`.
    """
    institution_name = unquote(institution_name).strip()
    rows = await run_query(
        UPDATE_STUDIED_AT,
        {
            "user_id": current_user["id"],
            "institution_name": institution_name,
            "start_year": start_year,
            "degree": body.degree,
            "department": body.department,
            "end_year": body.end_year,
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education record not found.",
        )

    row = rows[0]
    logger.info(
        "User %s updated education at %s (%s).",
        current_user["id"],
        institution_name,
        start_year,
    )
    return EducationItem(
        institution_name=row["institution_name"],
        institution_type=row["institution_type"],
        degree=row["degree"],
        department=row["department"],
        start_year=row["start_year"],
        end_year=row["end_year"],
    )


@router.delete(
    "/education/{institution_name}/{start_year}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an education record",
    responses={404: _404, 503: _503},
)
@handle_db_errors("delete_education")
async def delete_education(
    institution_name: str = Path(
        description="Exact institution name (URL-encoded if needed).",
        examples=["University of Cape Town"],
    ),
    start_year: int = Path(
        description="The `start_year` of the record to delete.",
        examples=[2018],
    ),
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Remove the `STUDIED_AT` relationship between the current user and the
    named institution for the given `start_year`.

    The Institution node itself is **not** deleted - it may be referenced
    by other users. Returns `404` if no matching record is found.
    """
    institution_name = unquote(institution_name).strip()
    rows = await run_query(
        DELETE_STUDIED_AT,
        {
            "user_id": current_user["id"],
            "institution_name": institution_name,
            "start_year": start_year,
        },
    )

    if not rows or rows[0]["deleted"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education record not found.",
        )

    logger.info(
        "User %s deleted education at %s (%s).",
        current_user["id"],
        institution_name,
        start_year,
    )


# ===========================================================================
# Employment
# ===========================================================================


@router.post(
    "/employment",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    summary="Add an employment record",
    responses={422: _422, 503: _503},
)
@handle_db_errors("add_employment")
async def add_employment(
    body: EmploymentRequest,
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """
    Attach a `WORKED_AT` edge between the current user and a Company node,
    creating the Company if it does not already exist (`MERGE`).

    The composite key for a record is **`company_name` + `start_year`**.
    Use this pair to target the record in `PATCH` and `DELETE` calls.

    For a **current role** set `is_current: true` and omit `end_year`.
    For a **past role** set `is_current: false` and include `end_year`.
    """
    await run_query(MERGE_COMPANY, {"name": body.company_name})
    await run_query(
        CREATE_WORKED_AT,
        {
            "user_id": current_user["id"],
            "company_name": body.company_name,
            "role": body.role,
            "start_year": body.start_year,
            "end_year": body.end_year,
            "is_current": body.is_current,
        },
    )
    logger.info(
        "User %s added employment at %s.", current_user["id"], body.company_name
    )
    return MessageResponse(detail="Employment record created.")


@router.get(
    "/employment",
    response_model=list[EmploymentItem],
    summary="List employment records",
    responses={503: _503},
)
@handle_db_errors("get_employment")
async def get_employment(
    current_user: dict = Depends(get_current_user),
) -> list[EmploymentItem]:
    """
    Return all employment records for the authenticated user, ordered by
    `start_year` descending (most recent first).

    Returns an empty list if no records have been added yet - not a `404`.
    """
    rows = await run_query(GET_EMPLOYMENT, {"user_id": current_user["id"]})
    return [
        EmploymentItem(
            company_name=row["company_name"],
            role=row["role"],
            start_year=row["start_year"],
            end_year=row["end_year"],
            is_current=row["is_current"],
        )
        for row in rows
    ]


@router.patch(
    "/employment/{company_name}/{start_year}",
    response_model=EmploymentItem,
    summary="Update an employment record",
    responses={404: _404, 422: _422, 503: _503},
)
@handle_db_errors("update_employment")
async def update_employment(
    company_name: str = Path(
        description="Exact company name as stored (URL-encoded if it contains spaces).",
        examples=["Acme Corp"],
    ),
    start_year: int = Path(
        description="The `start_year` of the record to update.",
        examples=[2022],
    ),
    body: EmploymentUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
) -> EmploymentItem:
    """
    Partially update one employment record identified by its composite key
    **`company_name` + `start_year`**.

    Common use cases:
    - Mark a role as finished: send `{ "is_current": false, "end_year": 2025 }`
    - Correct a job title: send `{ "role": "Staff Engineer" }`

    `company_name` and `start_year` are immutable - delete and re-add to
    correct them.

    **Path encoding**: URL-encode spaces - e.g. `Acme%20Corp`.
    """
    company_name = unquote(company_name).strip()
    rows = await run_query(
        UPDATE_WORKED_AT,
        {
            "user_id": current_user["id"],
            "company_name": company_name,
            "start_year": start_year,
            "role": body.role,
            "end_year": body.end_year,
            "is_current": body.is_current,
        },
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment record not found.",
        )

    row = rows[0]
    logger.info(
        "User %s updated employment at %s (%s).",
        current_user["id"],
        company_name,
        start_year,
    )
    return EmploymentItem(
        company_name=row["company_name"],
        role=row["role"],
        start_year=row["start_year"],
        end_year=row["end_year"],
        is_current=row["is_current"],
    )


@router.delete(
    "/employment/{company_name}/{start_year}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an employment record",
    responses={404: _404, 503: _503},
)
@handle_db_errors("delete_employment")
async def delete_employment(
    company_name: str = Path(
        description="Exact company name (URL-encoded if needed).",
        examples=["Acme Corp"],
    ),
    start_year: int = Path(
        description="The `start_year` of the record to delete.",
        examples=[2022],
    ),
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Remove the `WORKED_AT` relationship between the current user and the
    named company for the given `start_year`.

    The Company node itself is **not** deleted - it may be referenced by
    other users. Returns `404` if no matching record is found.
    """
    company_name = unquote(company_name).strip()
    rows = await run_query(
        DELETE_WORKED_AT,
        {
            "user_id": current_user["id"],
            "company_name": company_name,
            "start_year": start_year,
        },
    )

    if not rows or rows[0]["deleted"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employment record not found.",
        )

    logger.info(
        "User %s deleted employment at %s (%s).",
        current_user["id"],
        company_name,
        start_year,
    )
