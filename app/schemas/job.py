from typing import Dict, Optional

from pydantic import BaseModel

from app.models.job import JobStatus


# --------------------------
# Pydantic Schemas
# --------------------------
class JobCreate(BaseModel):
    name: str
    interval_seconds: int
    job_metadata: Optional[Dict] = {}


class JobUpdate(BaseModel):
    name: Optional[str] = None
    interval_seconds: Optional[int] = None
    job_metadata: Optional[Dict] = None
    status: Optional[JobStatus] = None
