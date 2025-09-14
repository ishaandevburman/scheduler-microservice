import traceback
import uuid
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.logger import logger, safe_log
from app.jobs.registry import register_job
from app.models.job import Job, JobStatus


@register_job("dummy_number_crunch")
def dummy_number_crunch(job_id: str, job_metadata: dict = None):
    try:
        with SessionLocal() as db_session:
            job_uuid = uuid.UUID(job_id)
            job = db_session.query(Job).filter(Job.id == job_uuid).first()

            if not job:
                safe_log(f"Job {job_id} not found in DB", level=logging.ERROR)
                return

            multiplier = job_metadata.get("multiplier", 1) if job_metadata else 1
            result = sum(range(100)) * multiplier

            job.update_last_run()
            db_session.commit()

            safe_log(
                f"[{datetime.now(timezone.utc)}] Executed Job {job_id} "
                f"| Result={result} | Metadata={job_metadata}"
            )

    except Exception as e:
        safe_log(f"Job {job_id} FAILED: {str(e)}", level=logging.ERROR)
        safe_log(traceback.format_exc(), level=logging.ERROR)

        try:
            with SessionLocal() as db_session:
                job_uuid = uuid.UUID(job_id)
                job = db_session.query(Job).filter(Job.id == job_uuid).first()
                if job:
                    job.status = JobStatus.FAILED
                    db_session.commit()
                    safe_log(f"Job {job_id} marked as FAILED in DB")
        except Exception as inner_e:
            safe_log(
                f"Failed to mark Job {job_id} as FAILED: {str(inner_e)}",
                level=logging.ERROR,
            )
            safe_log(traceback.format_exc(), level=logging.ERROR)

@register_job("print_hello")
def print_hello(job_id: str, job_metadata: dict = None):
    safe_log(f"Hello from Job {job_id}! Metadata={job_metadata}")
