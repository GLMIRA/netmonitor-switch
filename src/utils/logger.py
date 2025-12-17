import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import os

load_dotenv()


def setup_logging(
    level: str = os.getenv("LOG_LEVEL", "DEBUG"),
    log_file: str = os.getenv("LOG_FILE", "logs/app.log"),
    max_bytes: int = int(os.getenv("LOG_MAX_BYTES", 10485760)),
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", 5)),
) -> None:
    """Configure the global logging system with rotating file and console handlers.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file
        max_bytes: Maximum file size before rotation (bytes)
        backup_count: Number of backup files to keep
    """
    logger = logging.getLogger()
    if logger.handlers:
        return
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (use __name__ from the module)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
