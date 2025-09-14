from typing import Dict, Optional

from pydantic import BaseModel, model_validator

from app.models.job import JobStatus


# Create -> status optional
class JobCreate(BaseModel):
    name: str
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    job_metadata: Optional[Dict] = {}
    status: Optional[JobStatus] = JobStatus.ACTIVE

    @model_validator(mode="before")
    def validate_one_schedule(cls, values):
        interval = values.get("interval_seconds") is not None
        cron = values.get("cron_expression") is not None

        if interval == cron:  # both True or both False → invalid
            raise ValueError("Exactly one of 'interval_seconds' or 'cron_expression' must be provided")
        return values

# Partial update -> all optional
class JobUpdate(BaseModel):
    name: Optional[str] = None
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    job_metadata: Optional[Dict] = None
    status: Optional[JobStatus] = None

    @model_validator(mode="before")
    def validate_one_schedule(cls, values):
        interval = values.get("interval_seconds") is not None
        cron = values.get("cron_expression") is not None

        if interval and cron:  # both set → invalid
            raise ValueError("Only one of 'interval_seconds' or 'cron_expression' can be provided")
        return values
