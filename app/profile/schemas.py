"""
Pydantic schemas for the profile module.

No Cypher here - all queries live in queries.py.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

# Current year used for year-range validation
_CURRENT_YEAR = datetime.now().year


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------


class InstitutionType(StrEnum):
    university = "university"
    school = "school"
    college = "college"


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------


class ProfileUpdateRequest(BaseModel):
    """
    All fields are optional - only the ones you include will be updated.
    Omit a field entirely to leave it unchanged.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New display name.",
        examples=["Alice Mbeki"],
    )
    bio: str | None = Field(
        default=None,
        max_length=500,
        description="Short bio or headline shown on the profile card.",
        examples=["Senior engineer · open to opportunities"],
    )
    location: str | None = Field(
        default=None,
        max_length=100,
        description="City or region used in people-search filters.",
        examples=["London, UK"],
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "bio": "Senior engineer · open to opportunities",
                    "location": "London, UK",
                }
            ]
        },
    }


class ProfileResponse(BaseModel):
    """Full profile of the authenticated user."""

    id: str = Field(description="User UUID.")
    name: str = Field(description="Display name.")
    email: str = Field(description="Email address (lower-cased).")
    bio: str | None = Field(default=None, description="Optional bio or headline.")
    location: str | None = Field(default=None, description="Optional city / region.")
    connection_count: int = Field(
        description="Number of outgoing KNOWS relationships (direct connections)."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "name": "Alice Mbeki",
                    "email": "alice@example.com",
                    "bio": "Senior engineer · open to opportunities",
                    "location": "London, UK",
                    "connection_count": 12,
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------


class EducationRequest(BaseModel):
    """Body for POST /profile/education."""

    institution_name: str = Field(
        min_length=1,
        description="Exact name of the institution. A new Institution node is created if it does not already exist.",
        examples=["University of Cape Town"],
    )
    institution_type: InstitutionType = Field(
        description="Category of the institution.",
        examples=["university"],
    )
    degree: str = Field(
        min_length=1,
        description="Degree or qualification obtained.",
        examples=["BSc Computer Science"],
    )
    department: str = Field(
        min_length=1,
        description="Faculty or department.",
        examples=["Faculty of Science"],
    )
    start_year: int = Field(
        ge=1900,
        le=_CURRENT_YEAR,
        description="Year studies began.",
        examples=[2018],
    )
    end_year: int = Field(
        ge=1900,
        description="Year studies ended (may be in the future for ongoing programmes).",
        examples=[2022],
    )

    @model_validator(mode="after")
    def end_year_gte_start_year(self) -> EducationRequest:
        if self.end_year < self.start_year:
            msg = "end_year must be greater than or equal to start_year"
            raise ValueError(msg)
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "institution_name": "University of Cape Town",
                    "institution_type": "university",
                    "degree": "BSc Computer Science",
                    "department": "Faculty of Science",
                    "start_year": 2018,
                    "end_year": 2022,
                }
            ]
        }
    }


class EducationUpdateRequest(BaseModel):
    """
    All fields optional - only included fields are updated.
    `start_year` and `institution_name` are the record's composite key
    and cannot be changed; delete and re-add the record instead.
    """

    degree: str | None = Field(
        default=None,
        min_length=1,
        description="New degree label.",
        examples=["BSc (Hons) Computer Science"],
    )
    department: str | None = Field(
        default=None,
        min_length=1,
        description="New department name.",
        examples=["School of Engineering"],
    )
    end_year: int | None = Field(
        default=None,
        ge=1900,
        description="Corrected graduation year.",
        examples=[2023],
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"examples": [{"end_year": 2023}]},
    }


class EducationItem(BaseModel):
    """One education record returned in list or update responses."""

    institution_name: str = Field(description="Name of the institution.")
    institution_type: str = Field(
        description="Category: university, school, or college."
    )
    degree: str = Field(description="Degree or qualification.")
    department: str = Field(description="Faculty or department.")
    start_year: int = Field(description="Year studies began.")
    end_year: int = Field(description="Year studies ended.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "institution_name": "University of Cape Town",
                    "institution_type": "university",
                    "degree": "BSc Computer Science",
                    "department": "Faculty of Science",
                    "start_year": 2018,
                    "end_year": 2022,
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Employment
# ---------------------------------------------------------------------------


class EmploymentRequest(BaseModel):
    """Body for POST /profile/employment."""

    company_name: str = Field(
        min_length=1,
        description="Exact company name. A new Company node is created if it does not already exist.",
        examples=["Acme Corp"],
    )
    role: str = Field(
        min_length=1,
        description="Job title.",
        examples=["Senior Software Engineer"],
    )
    start_year: int = Field(
        ge=1900,
        le=_CURRENT_YEAR,
        description="Year employment began.",
        examples=[2022],
    )
    end_year: int | None = Field(
        default=None,
        ge=1900,
        description="Year employment ended. Required when `is_current` is `false`.",
        examples=[2024],
    )
    is_current: bool = Field(
        description="Set to `true` for a current role; `end_year` may then be omitted.",
        examples=[False],
    )

    @model_validator(mode="after")
    def validate_end_year(self) -> EmploymentRequest:
        if not self.is_current:
            if self.end_year is None:
                msg = "end_year is required when is_current is false"
                raise ValueError(msg)
            if self.end_year < self.start_year:
                msg = "end_year must be greater than or equal to start_year"
                raise ValueError(msg)
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "company_name": "Acme Corp",
                    "role": "Senior Software Engineer",
                    "start_year": 2022,
                    "end_year": 2024,
                    "is_current": False,
                }
            ]
        }
    }


class EmploymentUpdateRequest(BaseModel):
    """
    All fields optional - only included fields are updated.
    `company_name` and `start_year` are the composite key and cannot be changed.
    """

    role: str | None = Field(
        default=None,
        min_length=1,
        description="Updated job title.",
        examples=["Staff Software Engineer"],
    )
    end_year: int | None = Field(
        default=None,
        ge=1900,
        description="Year employment ended.",
        examples=[2025],
    )
    is_current: bool | None = Field(
        default=None,
        description="Update whether this is a current role.",
        examples=[False],
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "examples": [
                {
                    "role": "Staff Software Engineer",
                    "is_current": False,
                    "end_year": 2025,
                }
            ]
        },
    }


class EmploymentItem(BaseModel):
    """One employment record returned in list or update responses."""

    company_name: str = Field(description="Company name.")
    role: str = Field(description="Job title.")
    start_year: int = Field(description="Year employment began.")
    end_year: int | None = Field(
        default=None, description="Year employment ended, if applicable."
    )
    is_current: bool = Field(description="Whether this is an active role.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "company_name": "Acme Corp",
                    "role": "Senior Software Engineer",
                    "start_year": 2022,
                    "end_year": 2024,
                    "is_current": False,
                }
            ]
        }
    }
