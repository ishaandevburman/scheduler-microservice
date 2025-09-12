import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    interval_seconds = Column(Integer, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    job_metadata = Column(JSON, default={})
    status = Column(SqlEnum(JobStatus), default=JobStatus.ACTIVE)

    def __repr__(self):
        return f"<Job(id={self.id}, name={self.name}, interval={self.interval_seconds}s, status={self.status})>"

    def update_last_run(self):
        """Update last_run_at and compute next_run_at (UTC-aware)."""
        now = datetime.now(timezone.utc)
        self.last_run_at = now
        if self.interval_seconds:
            self.next_run_at = now + timedelta(seconds=self.interval_seconds)
