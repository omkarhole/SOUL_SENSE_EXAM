from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ArchiveRequest(BaseModel):
    password: str = Field(..., min_length=8, description="Password to encrypt the ZIP archive.")
    include_pdf: bool = True
    include_csv: bool = True
    include_json: bool = True

class ArchiveResponse(BaseModel):
    job_id: str
    status: str
    message: str

class PurgeResponse(BaseModel):
    message: str
    purge_date: datetime
    can_undo_until: datetime

class UndoPurgeResponse(BaseModel):
    message: str
    status: str
