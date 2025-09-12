from fastapi import FastAPI

from app.api import jobs
from app.core.database import SessionLocal, engine
from app.core.scheduler import scheduler_manager
from app.models.job import Base

app = FastAPI(title="Interval Scheduler Microservice")

# Create tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(jobs.router)

# Load and schedule existing active jobs from DB
with SessionLocal() as db:
    scheduler_manager.load_existing_jobs(db_session=db)
