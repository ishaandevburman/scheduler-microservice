import uuid

from app.models.job import Job, JobStatus


class JobService:
    def __init__(self, db_session):
        self.db = db_session

    def get_all_jobs(self):
        return self.db.query(Job).all()

    def get_job(self, job_id: uuid.UUID):
        return self.db.query(Job).filter(Job.id == job_id).first()

    def create_job(self, job_data):
        job_data.setdefault("status", JobStatus.ACTIVE)
        job = Job(**job_data)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
