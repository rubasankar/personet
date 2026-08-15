from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class SignupRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Full display name shown on the profile.",
        examples=["Alice Mbeki"],
    )
    email: EmailStr = Field(
        max_length=254,
        description="Email address used to log in. Stored in lower-case.",
        examples=["alice@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plain-text password - hashed with bcrypt before storage.",
        examples=["s3cr3tP@ssword"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Alice Mbeki",
                    "email": "alice@example.com",
                    "password": "s3cr3tP@ssword",
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        max_length=254,
        description="Registered email address.",
        examples=["alice@example.com"],
    )
    password: str = Field(
        min_length=1,
        description="Account password.",
        examples=["s3cr3tP@ssword"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "alice@example.com",
                    "password": "s3cr3tP@ssword",
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Returned on successful signup or login.
    The JWT is delivered via cookie, not in this body."""

    id: str = Field(description="UUID of the newly authenticated user.")
    name: str = Field(description="Display name.")
    email: str = Field(description="Email address (lower-cased).")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "name": "Alice Mbeki",
                    "email": "alice@example.com",
                }
            ]
        }
    }
