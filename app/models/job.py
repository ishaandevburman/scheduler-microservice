import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import JSON, CheckConstraint, Column, DateTime
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
    interval_seconds = Column(Integer, nullable=True)
    cron_expression = Column(String, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    job_metadata = Column(JSON, default={})
    status = Column(SqlEnum(JobStatus), default=JobStatus.ACTIVE)

    __table_args__ = (
        CheckConstraint(
            "(interval_seconds IS NOT NULL AND cron_expression IS NULL) OR "
            "(interval_seconds IS NULL AND cron_expression IS NOT NULL)",
            name="check_interval_or_cron_only"
        ),
    )

    def __repr__(self):
        if self.interval_seconds is not None:
            schedule_part = f"interval={self.interval_seconds}s"
        elif self.cron_expression is not None:
            schedule_part = f"cron='{self.cron_expression}'"

        last_run_str = self.last_run_at.isoformat() if self.last_run_at else "None"
        next_run_str = self.next_run_at.isoformat() if self.next_run_at else "None"
        return (
            f"<Job(id={self.id}, name='{self.name}', {schedule_part}, "
            f"last_run_at={last_run_str}, next_run_at={next_run_str}, status={self.status})>"
        )


    def update_last_run(self):
        """Update last_run_at and compute next_run_at (UTC-aware)."""
        now = datetime.now(timezone.utc)
        self.last_run_at = now

        if self.interval_seconds is not None:
            self.next_run_at = now + timedelta(seconds=self.interval_seconds)
        elif self.cron_expression is not None:
            try:
                trigger = CronTrigger.from_crontab(self.cron_expression, timezone=timezone.utc)
                self.next_run_at = trigger.get_next_fire_time(previous_fire_time=now, now=now)
            except Exception:
                self.next_run_at = None
        else:
            self.next_run_at = None

    def get_trigger(self):
        if self.interval_seconds is not None:
            return IntervalTrigger(seconds=self.interval_seconds, timezone=timezone.utc)
        elif self.cron_expression is not None:
            return CronTrigger.from_crontab(self.cron_expression, timezone=timezone.utc)
        else:
            return None
