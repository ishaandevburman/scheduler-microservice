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

    def add_job(self, job, func, **kwargs):

        self.scheduler.add_job(
            func=func,
            trigger="interval",
            id=str(job.id),
            seconds=job.interval_seconds,
            **kwargs,
        )
        safe_log(f"Scheduled job {job.id} every {job.interval_seconds} seconds")

    def load_existing_jobs(self, db_session):
        """Load and schedule existing active jobs from DB on startup."""

        jobs = db_session.query(Job).filter(Job.status == JobStatus.ACTIVE).all()
        for job in jobs:
            self.remove_existing_job(job)
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
