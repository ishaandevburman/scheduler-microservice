import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jobs import dummy_number_crunch
from app.core.logger import logger
from app.core.scheduler import scheduler_manager
from app.models.job import Job, JobStatus

router = APIRouter()


# --------------------------
# Pydantic Schemas
# --------------------------
class JobCreate(BaseModel):
    name: str
    interval_seconds: int
    job_metadata: Optional[Dict] = {}


class JobUpdate(BaseModel):
    name: Optional[str]
    interval_seconds: Optional[int]
    job_metadata: Optional[Dict]
    status: Optional[JobStatus]


# --------------------------
# API Endpoints
# --------------------------


@router.post("/jobs")
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


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return jobs


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/jobs/{job_id}")
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


@router.patch("/jobs/{job_id}")
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


@router.post("/jobs/{job_id}/pause")
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


@router.post("/jobs/{job_id}/resume")
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


@router.delete("/jobs/{job_id}")
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


@router.delete("/jobs")
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
