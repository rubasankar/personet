"""
Shared response schemas used across multiple routers.
"""

from pydantic import BaseModel
from pydantic import Field


class MessageResponse(BaseModel):
    """Generic acknowledgement response returned by write endpoints."""

    detail: str = Field(
        description="Human-readable confirmation message.",
        examples=["Education record created."],
    )
