import traceback
import uuid
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.logger import logger, safe_log
from app.models.job import Job, JobStatus


def dummy_number_crunch(job_id: str, job_metadata: dict = None):
    """Simulate computation with failure handling."""
    try:
        with SessionLocal() as db_session:
            # Convert string to UUID
            job_uuid = uuid.UUID(job_id)
            job = db_session.query(Job).filter(Job.id == job_uuid).first()

            if not job:
                safe_log(f"Job {job_id} not found in DB", level=logger.error)
                return

            # Simulate number crunching
            multiplier = job_metadata.get("multiplier", 1) if job_metadata else 1
            result = sum(range(100)) * multiplier

            # Update last run timestamp
            job.update_last_run()
            db_session.commit()

            safe_log(
                f"[{datetime.now(timezone.utc)}] Executing Job {job_id} | Result={result} | Metadata={job_metadata}"
            )

    except Exception as e:
        safe_log(f"[{datetime.now(timezone.utc)}] Job {job_id} FAILED: {str(e)}", level=logger.error)
        safe_log(traceback.format_exc(), level=logger.error)

        # Mark job as FAILED in DB
        try:
            with SessionLocal() as db_session:
                job_uuid = uuid.UUID(job_id)
                job = db_session.query(Job).filter(Job.id == job_uuid).first()
                if job:
                    job.status = JobStatus.FAILED
                    db_session.commit()
                    safe_log(f"Job {job_id} marked as FAILED in DB")
        except Exception as inner_e:
            safe_log(f"Failed to mark Job {job_id} as FAILED in DB: {str(inner_e)}", level=logger.error)
            safe_log(traceback.format_exc(), level=logger.error)
