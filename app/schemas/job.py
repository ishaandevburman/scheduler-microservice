from typing import Dict, Optional

from pydantic import BaseModel

from app.models.job import JobStatus


# Create → status optional
class JobCreate(BaseModel):
    name: str
    interval_seconds: int
    job_metadata: Optional[Dict] = {}
    status: Optional[JobStatus] = JobStatus.ACTIVE

# Full replace → status required
class JobReplace(BaseModel):
    name: str
    interval_seconds: int
    job_metadata: Optional[Dict] = {}
    status: JobStatus  # required

# Partial update → all optional
class JobUpdate(BaseModel):
    name: Optional[str] = None
    interval_seconds: Optional[int] = None
    job_metadata: Optional[Dict] = None
    status: Optional[JobStatus] = None