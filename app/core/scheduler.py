from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from app.core.config import settings
from app.core.database import engine
from app.core.logger import safe_log
from app.jobs.registry import JOB_REGISTRY
from app.models.job import Job, JobStatus


class SchedulerManager:
    def __init__(self, db_engine):
        jobstores = {"default": SQLAlchemyJobStore(engine=db_engine)}
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores, job_defaults=settings.SCHEDULER_JOB_DEFAULTS
        )
        self.scheduler.start()
        safe_log("Scheduler started")
        safe_log(f"Loaded functions {JOB_REGISTRY}")

    def add_job(self, job: Job):
        trigger = job.get_trigger()
        if not trigger:
            safe_log(f"Job {job.id} has no valid schedule. Skipping.")
            return

        if job.next_run_at is None:
            safe_log(f"Job {job.id} has no computed next_run_at. Skipping.")
            return

        func = JOB_REGISTRY.get(job.function_name)
        if not func:
            safe_log(
                f"Job {job.id} has unknown function '{job.function_name}'. Skipping.",
                level=logging.ERROR,  # fixed logging level issue
            )
            return

        try:
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=str(job.id),
                kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
            )
            safe_log(
                f"Scheduled job {job.id} "
                f"({'interval' if job.interval_seconds else 'cron'}) "
                f"with function '{job.function_name}'"
            )
        except Exception as e:
            safe_log(f"Failed to schedule job {job.id}: {e}", level=logging.ERROR)

    def load_existing_jobs(self, db_session):
        """Load and schedule existing active jobs from DB on startup."""
        jobs = db_session.query(Job).filter(Job.status == JobStatus.ACTIVE).all()
        for job in jobs:
            try:
                self.add_job(job)
            except Exception as e:
                safe_log(f"Failed to load job {job.id}: {e}", level=logging.ERROR)

    def remove_existing_job(self, job: Job):
        """Remove a job from scheduler if it already exists."""
        job_id_str = str(job.id)
        existing_job = self.scheduler.get_job(job_id_str)
        if existing_job:
            safe_log(
                f"Job {job_id_str} already exists. Removing old job before rescheduling."
            )
            try:
                self.scheduler.remove_job(job_id_str)
            except Exception as e:
                safe_log(f"Failed to remove existing job {job_id_str}: {e}", level=logging.ERROR)


# Singleton instance for global use
scheduler_manager = SchedulerManager(engine)
