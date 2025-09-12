from concurrent.futures import ThreadPoolExecutor

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./scheduler.db"  # or PostgreSQL URL
    SCHEDULER_JOB_DEFAULTS: dict = {"coalesce": True, "max_instances": 1}


settings = Settings()
