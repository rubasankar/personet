"""
Pydantic schemas for the network module.
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConnectionContext(StrEnum):
    classmate = "classmate"
    colleague = "colleague"
    family = "family"
    friend = "friend"


class Closeness(StrEnum):
    close = "close"
    acquaintance = "acquaintance"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ConnectRequest(BaseModel):
    """Body for POST /network/connect/{target_user_id}."""

    context: ConnectionContext = Field(
        description="How you know this person.",
        examples=["colleague"],
    )
    since: date | None = Field(
        default=None,
        description="Optional ISO 8601 date when you first met (YYYY-MM-DD).",
        examples=["2022-06-01"],
    )
    closeness: Closeness = Field(
        default=Closeness.acquaintance,
        description="Strength of the relationship. Defaults to `acquaintance`.",
        examples=["acquaintance"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "context": "colleague",
                    "since": "2022-06-01",
                    "closeness": "acquaintance",
                }
            ]
        }
    }


class UpdateConnectionRequest(BaseModel):
    """Body for PATCH /network/connect/{target_user_id}. All fields optional."""

    context: ConnectionContext | None = Field(
        default=None,
        description="Updated relationship category.",
        examples=["friend"],
    )
    since: date | None = Field(
        default=None,
        description="Updated date when you first met (YYYY-MM-DD).",
        examples=["2019-03-15"],
    )
    closeness: Closeness | None = Field(
        default=None,
        description="Updated relationship strength.",
        examples=["close"],
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"examples": [{"closeness": "close"}]},
    }


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class UserSearchItem(BaseModel):
    """One person returned by GET /network/users."""

    id: str = Field(
        description="User UUID. Use this as `target_user_id` in connect and path endpoints.",
    )
    name: str = Field(description="Display name.")
    location: str | None = Field(default=None, description="City or region, if set.")
    companies: list[str] = Field(
        description="Companies this person has worked at (used to confirm you have the right person).",
    )
    institutions: list[str] = Field(
        description="Institutions this person has studied at.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "name": "Alice Mbeki",
                    "location": "London, UK",
                    "companies": ["Acme Corp", "Startup XYZ"],
                    "institutions": ["University of Cape Town"],
                }
            ]
        }
    }


class ConnectionItem(BaseModel):
    """One direct connection returned by GET /network/connections."""

    id: str = Field(description="User UUID.")
    name: str = Field(description="Display name.")
    location: str | None = Field(default=None, description="City or region, if set.")
    context: str = Field(description="How you know this person.")
    since: str | None = Field(
        default=None, description="ISO 8601 date when you first met."
    )
    closeness: str = Field(description="Relationship strength: close or acquaintance.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "name": "Bob Nkosi",
                    "location": "Cape Town, ZA",
                    "context": "colleague",
                    "since": "2022-06-01",
                    "closeness": "close",
                }
            ]
        }
    }


class SuggestionItem(BaseModel):
    """One suggested connection from GET /network/suggestions."""

    id: str = Field(description="User UUID.")
    name: str = Field(description="Display name.")
    location: str | None = Field(default=None, description="City or region, if set.")
    shared_context: list[str] = Field(
        description="Names of companies or institutions you both have in common.",
    )
    overlap_score: int = Field(
        description="Number of shared companies/institutions - higher means stronger suggestion.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "name": "Bob Nkosi",
                    "location": "Cape Town, ZA",
                    "shared_context": ["Acme Corp", "University of Cape Town"],
                    "overlap_score": 2,
                }
            ]
        }
    }


class PathNode(BaseModel):
    """A single person in a connection chain."""

    id: str = Field(description="User UUID.")
    name: str = Field(description="Display name.")


# ---------------------------------------------------------------------------
# Intro finder schemas
# ---------------------------------------------------------------------------


class IntroType(StrEnum):
    direct_context = "direct_context"  # share a company/institution - talk directly
    knows_path = "knows_path"  # KNOWS chain exists (may also have direct_context)
    suggested_intro = "suggested_intro"  # no path, but here's a bridge person
    unreachable = "unreachable"  # nothing found


class IntroSuggestion(BaseModel):
    """A bridge person who can introduce you to the target."""

    id: str = Field(description="Bridge person's UUID.")
    name: str = Field(description="Bridge person's display name.")
    location: str | None = Field(default=None)
    knows_distance: int = Field(
        description=(
            "When reach_type='knows': KNOWS hops from you to this person. "
            "When reach_type='context': KNOWS hops from this person to the target."
        )
    )
    shared_node_name: str = Field(
        description="The company or institution connecting you to this bridge person."
    )
    shared_node_type: str = Field(description="'Company' or 'Institution'.")
    reach_type: str = Field(
        description=(
            "'knows' = you already know this person (via KNOWS chain), they share context with target. "
            "'context' = you share a company/institution with them, they have a KNOWS path to target."
        )
    )
    chain_to_target: list[PathNode] = Field(
        default=[],
        description=(
            "Ordered KNOWS chain from this bridge person to the target (inclusive). "
            "Use this to render 'Alice -> Charlie -> Bob' so the user understands "
            "the full onward route after connecting with the bridge person."
        ),
    )


class IntroResponse(BaseModel):
    """
    Result of GET /network/intro/{target_user_id}.

    Multiple fields can be populated at once - e.g. a knows_path response
    can also carry shared_context if you share a company/institution with
    the target.  Read `type` to know the primary result, then render
    whichever extra fields are non-empty as supplementary information.
    """

    type: IntroType = Field(description="Primary result type.")

    # Always populated when you share a company/institution with the target
    shared_context: list[str] = Field(
        default=[],
        description="Names of shared companies/institutions (non-empty when type=direct_context or alongside knows_path).",
    )

    # Populated when a KNOWS chain exists
    chain: list[PathNode] = Field(
        default=[],
        description="Ordered list of users in the KNOWS path (populated when type=knows_path).",
    )
    hops: int = Field(
        default=0,
        description="Number of KNOWS hops (populated when type=knows_path).",
    )
    via_close_only: bool = Field(
        default=False,
        description="True when every hop in the chain is a close connection.",
    )

    # Populated when no KNOWS path exists but bridge people were found
    suggestions: list[IntroSuggestion] = Field(
        default=[],
        description="Bridge people to connect with first (populated when type=suggested_intro).",
    )
