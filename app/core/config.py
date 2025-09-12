from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    ENV: str = "development"  # "development" or "production"
    DATABASE_URL: str = "sqlite:///./scheduler.db"
    LOG_LEVEL: str = "DEBUG"
    SCHEDULER_JOB_DEFAULTS: dict = {"coalesce": True, "max_instances": 1}

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Adjust database URL for production if needed
if settings.ENV.lower() == "production":
    if not settings.DATABASE_URL.startswith("postgresql"):
        raise ValueError("In production, DATABASE_URL must be a PostgreSQL URL with psycopg2.")
