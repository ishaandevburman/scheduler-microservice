import logging
from logging.handlers import RotatingFileHandler

# Create logger
logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

# Rotating file handler: 5 MB max, 3 backups
file_handler = RotatingFileHandler(
    "scheduler.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
