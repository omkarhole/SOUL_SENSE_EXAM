from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TeamVisionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., description="The team vision document content")

class TeamVisionCreate(TeamVisionBase):
    team_id: str

class TeamVisionUpdate(TeamVisionBase):
    version: int = Field(..., description="Fencing token (current version) to prevent lost updates")
    lock_value: str = Field(..., description="The acquired Redlock value to prove ownership")

class TeamVisionResponse(TeamVisionBase):
    id: int
    team_id: str
    version: int
    updated_at: str
    last_modified_by_id: Optional[int] = None
    lock_status: Optional[dict] = None # Information about current lock holder

class LockAcquireResponse(BaseModel):
    success: bool
    lock_value: Optional[str] = None
    message: str
    expires_in: int = 30 # Seconds

class LockReleaseRequest(BaseModel):
    lock_value: str
