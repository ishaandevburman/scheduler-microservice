from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.job import JobStatus


class JobCreate(BaseModel):
    name: str
    function_name: str  
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    job_metadata: Dict = Field(default_factory=dict)
    status: Optional[JobStatus] = JobStatus.ACTIVE

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def validate_one_schedule(cls, values: dict) -> dict:
        interval = values.get("interval_seconds") is not None
        cron = values.get("cron_expression") is not None

        # Both True or both False -> invalid
        if interval == cron:
            raise ValueError(
                "Exactly one of 'interval_seconds' or 'cron_expression' must be provided"
            )
        return values


class JobUpdate(BaseModel):
    name: Optional[str] = None
    function_name: Optional[str] = None
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    job_metadata: Optional[Dict] = None
    status: Optional[JobStatus] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def validate_one_schedule(cls, values: dict) -> dict:
        interval = values.get("interval_seconds") is not None
        cron = values.get("cron_expression") is not None

        # In PATCH we only block if both are set together
        if interval and cron:
            raise ValueError(
                "Only one of 'interval_seconds' or 'cron_expression' can be provided"
            )
        return values
