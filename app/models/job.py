import logging
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

from app.core.logger import safe_log

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
    function_name = Column(String, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    job_metadata = Column(JSON, default=dict)
    status = Column(SqlEnum(JobStatus), nullable=False, default=JobStatus.ACTIVE)


    __table_args__ = (
        CheckConstraint(
            "(interval_seconds IS NOT NULL AND cron_expression IS NULL) OR "
            "(interval_seconds IS NULL AND cron_expression IS NOT NULL)",
            name="check_interval_or_cron_only",
        ),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Automatically compute next_run_at if schedule exists
        self.next_run_at = self.compute_next_run()

    def __repr__(self):
        if self.interval_seconds is not None:
            schedule_part = f"interval={self.interval_seconds}s"
        elif self.cron_expression is not None:
            schedule_part = f"cron='{self.cron_expression}'"
        else:
            schedule_part = "unscheduled"

        last_run_str = self.last_run_at.isoformat() if self.last_run_at else "None"
        next_run_str = self.next_run_at.isoformat() if self.next_run_at else "None"
        
        return (
            f"<Job(id={self.id}, name='{self.name}', {schedule_part}, "
            f"last_run_at={last_run_str}, next_run_at={next_run_str}, status={self.status})>"
        )


    def compute_next_run(self, from_time: datetime = None):
        """Compute the next_run_at from interval or cron, without touching last_run_at."""
        now = from_time or datetime.now(timezone.utc)

        if self.interval_seconds:
            return now + timedelta(seconds=self.interval_seconds)
        elif self.cron_expression:
            try:
                trigger = CronTrigger.from_crontab(self.cron_expression, timezone=timezone.utc)
                return trigger.get_next_fire_time(previous_fire_time=now, now=now)
            except Exception:
                return None
        return None

    def update_last_run(self):
        """Set last_run_at and advance next_run_at."""
        now = datetime.now(timezone.utc)
        self.last_run_at = now
        self.next_run_at = self.compute_next_run(from_time=now)

    def get_trigger(self):
        if self.interval_seconds:
            return IntervalTrigger(seconds=self.interval_seconds, timezone=timezone.utc)
        if self.cron_expression:
            try:
                return CronTrigger.from_crontab(self.cron_expression, timezone=timezone.utc)
            except Exception as e:
                safe_log(
                    f"Job {self.id} has invalid cron expression '{self.cron_expression}': {e}",
                    level=logging.ERROR
                )
                return None
        return None
