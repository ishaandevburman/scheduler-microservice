import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import engine
from app.core.jobs import dummy_number_crunch
from app.core.logger import logger, safe_log
from app.models.job import Job, JobStatus


class SchedulerManager:
    def __init__(self, db_engine):
        jobstores = {"default": SQLAlchemyJobStore(engine=db_engine)}
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores, job_defaults=settings.SCHEDULER_JOB_DEFAULTS
        )
        self.scheduler.start()
        safe_log("Scheduler started")

    def add_job(self, job: Job, func, **kwargs):
        """Schedule a job (interval or cron) based on Job model."""
        trigger = job.get_trigger()
        if not trigger:
            safe_log(f"Job {job.id} has no valid schedule. Skipping.")
            return
        
        if job.next_run_at is None:
            safe_log(f"Job {job.id} has no computed next_run_at. Skipping.")
            return

        # Schedule the job
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=str(job.id),
            **kwargs,
        )

        safe_log(
            f"Scheduled job {job.id} "
            f"({'interval' if job.interval_seconds else 'cron'})"
        )

    def load_existing_jobs(self, db_session):
        """Load and schedule existing active jobs from DB on startup."""
        jobs = db_session.query(Job).filter(Job.status == JobStatus.ACTIVE).all()
        for job in jobs:
            self.add_job(
                job,
                func=dummy_number_crunch,
                kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
            )
    
    def remove_existing_job(self, job):
        job_id_str = str(job.id)

        # Remove existing job if it exists
        existing_job = self.scheduler.get_job(job_id_str)
        if existing_job:
            safe_log(
                f"Job {job_id_str} already exists. Removing old job before scheduling."
            )
            self.scheduler.remove_job(job_id_str)



# Singleton instance for global use
scheduler_manager = SchedulerManager(engine)
