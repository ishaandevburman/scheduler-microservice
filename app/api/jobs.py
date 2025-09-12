import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jobs import dummy_number_crunch
from app.core.logger import logger
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
    jobs = db.query(Job).all()
    return jobs


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
        job_metadata=job_in.job_metadata,
        status=JobStatus.ACTIVE,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Schedule the job
    scheduler_manager.add_job(
        job=job,
        func=dummy_number_crunch,
        kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
    )
    logger.info(f"Job {job.id} created and scheduled")
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

    # Update all fields
    job.name = job_in.name
    job.interval_seconds = job_in.interval_seconds
    job.job_metadata = job_in.job_metadata
    job.status = JobStatus.ACTIVE
    db.commit()

    # Reschedule
    scheduler_manager.add_job(
        job=job,
        func=dummy_number_crunch,
        kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
    )
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
    if job_in.job_metadata is not None:
        job.job_metadata = job_in.job_metadata
    if job_in.status is not None:
        job.status = job_in.status
    db.commit()

    # Reschedule if active
    if job.status == JobStatus.ACTIVE:
        scheduler_manager.add_job(
            job=job,
            func=dummy_number_crunch,
            kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
        )
    else:
        # Remove from scheduler if not active
        if scheduler_manager.scheduler.get_job(str(job.id)):
            scheduler_manager.scheduler.remove_job(str(job.id))

    return job


@router.post(
    "/jobs/{job_id}/pause",
    summary="Pause a job",
    description="Temporarily pause a job. "
                "The job will remain in the database but will not execute until resumed."
)
def pause_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.PAUSED
    db.commit()

    # Remove from scheduler
    if scheduler_manager.scheduler.get_job(job_id):
        scheduler_manager.scheduler.remove_job(job_id)

    return {"message": f"Job {job_id} paused"}


@router.post(
    "/jobs/{job_id}/resume",
    summary="Resume a job",
    description="Reactivate a paused or inactive job. "
                "The job will be rescheduled and continue running at its defined interval."
)
def resume_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.ACTIVE
    db.commit()

    # Reschedule
    scheduler_manager.add_job(
        job=job,
        func=dummy_number_crunch,
        kwargs={"job_id": str(job.id), "job_metadata": job.job_metadata},
    )

    return {"message": f"Job {job_id} resumed"}


@router.delete(
    "/jobs/{job_id}",
    summary="Delete a single job",
    description="⚠️ Permanently delete a single job by UUID. "
                "Removes it from both the database and the scheduler. "
                "Requires `?confirm=true` query parameter."
)
def delete_job(
    job_id: str,
    confirm: bool = Query(
        default=False, description="Set to true to confirm deletion of this job"
    ),
    db: Session = Depends(get_db),
):
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

    # Remove from scheduler if exists
    job_id_str = str(job.id)
    if scheduler_manager.scheduler.get_job(job_id_str):
        scheduler_manager.scheduler.remove_job(job_id_str)

    # Remove from DB
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
def delete_all_jobs(
    confirm: bool = Query(
        default=False, description="Set to true to confirm deletion of ALL jobs"
    ),
    db: Session = Depends(get_db),
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Use ?confirm=true to delete all jobs.",
        )

    jobs = db.query(Job).all()
    for job in jobs:
        job_id_str = str(job.id)

        # Remove from scheduler if it exists
        if scheduler_manager.scheduler.get_job(job_id_str):
            scheduler_manager.scheduler.remove_job(job_id_str)

        # Remove from DB
        db.delete(job)

    db.commit()
    return {"message": "All jobs deleted successfully"}
