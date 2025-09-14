import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jobs import dummy_number_crunch
from app.core.logger import safe_log
from app.core.scheduler import scheduler_manager
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate

router = APIRouter()


@router.get(
    "/jobs",
    summary="List all jobs",
    description="Returns a list of all scheduled jobs including their details such as name, interval, status, and metadata."
)
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()


@router.get(
    "/jobs/{job_id}",
    summary="Get job details",
    description="Fetch details of a specific job by its UUID. Includes scheduling information and metadata."
)
def get_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post(
    "/jobs",
    summary="Create a new job",
    description="Create a new job with a name, interval, metadata, and status. "
                "Jobs are scheduled immediately if set to `active`."
)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    job = Job(
        name=job_in.name,
        interval_seconds=job_in.interval_seconds,
        cron_expression=job_in.cron_expression,
        job_metadata=job_in.job_metadata,
        status=job_in.status or JobStatus.ACTIVE,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if job.status == JobStatus.ACTIVE:
        scheduler_manager.add_job(
            job=job,
            func=dummy_number_crunch,
            kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
        )
        safe_log(f"Job {job.id} created and scheduled")
    else:
        safe_log(f"Job {job.id} created but not active, skipping scheduling")
    return job


@router.put(
    "/jobs/{job_id}",
    summary="Replace a job",
    description="Completely replace a job definition. "
                "All fields must be provided. Missing fields will be reset."
)
def replace_job(job_id: str, job_in: JobCreate, db: Session = Depends(get_db)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Replace all fields
    job.name = job_in.name
    job.interval_seconds = job_in.interval_seconds
    job.cron_expression = job_in.cron_expression
    job.job_metadata = job_in.job_metadata
    job.status = job_in.status
    db.commit()

    scheduler_manager.remove_existing_job(job)

    # Reschedule only if active
    # Schedule the job
    if job.status == JobStatus.ACTIVE:
        scheduler_manager.add_job(
            job=job,
            func=dummy_number_crunch,
            kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
        )
        safe_log(f"Job {job.id} replaced and scheduled")
    else:
        safe_log(f"Job {job.id} replaced but not active, skipping scheduling")
    return job


@router.patch(
    "/jobs/{job_id}",
    summary="Update job (partial)",
    description="Update one or more fields of a job (e.g., name, interval, metadata, status). "
                "Fields not provided remain unchanged."
)
def patch_job(job_id: str, job_in: JobUpdate, db: Session = Depends(get_db)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update only provided fields
    if job_in.name is not None:
        job.name = job_in.name
    if job_in.interval_seconds is not None:
        job.interval_seconds = job_in.interval_seconds
        job.cron_expression = None
    if job_in.cron_expression is not None:
        job.cron_expression = job_in.cron_expression
        job.interval_seconds = None
    if job_in.job_metadata is not None:
        job.job_metadata = job_in.job_metadata
    if job_in.status is not None:
        job.status = job_in.status

    db.commit()
    
    scheduler_manager.remove_existing_job(job)

    # Reschedule if active
    # Schedule the job
    if job.status == JobStatus.ACTIVE:
        scheduler_manager.add_job(
            job=job,
            func=dummy_number_crunch,
            kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
        )
        safe_log(f"Job {job.id} updated and scheduled")
    else:
        safe_log(f"Job {job.id} updated but not active, skipping scheduling")
    return job


@router.delete(
    "/jobs/{job_id}",
    summary="Delete a single job",
    description="⚠️ Permanently delete a single job by UUID. "
                "Removes it from both the database and the scheduler. "
                "Requires `?confirm=true` query parameter."
)
def delete_job(job_id: str, confirm: bool = Query(False), db: Session = Depends(get_db)):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Use ?confirm=true to delete this job.",
        )

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    scheduler_manager.remove_existing_job(job)
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully"}


@router.delete(
    "/jobs",
    summary="Delete all jobs",
    description="⚠️ Permanently delete **all jobs** from the system. "
                "Removes them from both the database and the scheduler. "
                "Requires `?confirm=true` query parameter."
)
def delete_all_jobs(confirm: bool = Query(False), db: Session = Depends(get_db)):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required (?confirm=true)")

    jobs = db.query(Job).all()
    for job in jobs:
        scheduler_manager.remove_existing_job(job)
        db.delete(job)
    db.commit()
    return {"message": "All jobs deleted successfully"}
