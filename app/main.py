from fastapi import FastAPI

import app.jobs.builtin
from app.api import jobs
from app.core.database import SessionLocal, engine
from app.core.scheduler import scheduler_manager
from app.models.job import Base

# Create tables
Base.metadata.create_all(bind=engine)

# Load and schedule existing active jobs from DB
with SessionLocal() as db:
    scheduler_manager.load_existing_jobs(db_session=db)

app = FastAPI(title="Interval Scheduler Microservice", version="0.1.0")

# Include routes
app.include_router(jobs.router)
