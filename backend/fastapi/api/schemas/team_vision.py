"""
Pydantic schemas for Team Vision collaborative document management.
File: api/schemas/team_vision.py  (matches PR description references)
"""
from pydantic import BaseModel, Field
from typing import Optional


class TeamVisionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., description="The team vision document content")


class TeamVisionCreate(TeamVisionBase):
    team_id: str


class TeamVisionUpdate(TeamVisionBase):
    version: int = Field(
        ...,
        description="Fencing token — the current document version. Must match the DB version exactly."
    )
    lock_value: str = Field(
        ...,
        description=(
            "Exact lock token returned by POST /lock. "
            "Validated against the active Redis lease value before the write is accepted."
        )
    )


class TeamVisionResponse(TeamVisionBase):
    id: int
    team_id: str
    version: int
    updated_at: str
    last_modified_by_id: Optional[int] = None
    lock_status: Optional[dict] = None  # Tells the UI who holds the lock (for read-only mode)


class LockAcquireResponse(BaseModel):
    success: bool
    lock_value: Optional[str] = None  # Client must store and re-send on every PUT and /renew
    message: str
    expires_in: int = 30  # TTL in seconds


class LockReleaseRequest(BaseModel):
    lock_value: str = Field(..., description="Exact token to verify ownership before releasing")


class LockRenewRequest(BaseModel):
    lock_value: str = Field(..., description="Exact token to verify ownership before renewing TTL")
    extend_by_seconds: int = Field(
        default=30, ge=5, le=300,
        description="Seconds to extend the lock TTL. Client should call every ~20s when TTL=30s."
    )


class LockRenewResponse(BaseModel):
    success: bool
    message: str
    new_expires_in: int = 0
