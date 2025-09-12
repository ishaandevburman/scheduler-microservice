import logging
import threading
from logging.handlers import RotatingFileHandler

# Create logger
logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

# Ensure only one handler is added (important if module is re-imported)
if not logger.handlers:
    # Rotating file handler: 5 MB max, 3 backups
    file_handler = RotatingFileHandler(
        "scheduler.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Make logging thread-safe
    file_handler.lock = threading.RLock()

    logger.addHandler(file_handler)

# Optional: Safe logging wrapper for jobs
def safe_log(message, level=logging.INFO):
    try:
        logger.log(level, message)
    except ValueError:
        # Stream might be closed; safely ignore
        pass
