import logging
import sys
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging(level: str = "INFO", log_file: str = "logs/app.log") -> None:
    """
    Configure structured logging for both console and file output.

    Args:
        level: Logging level as string (e.g. "DEBUG", "INFO", "WARNING").
        log_file: Path to the log file (directories will be created if needed).
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Shared formatter with safe fallback for missing extra fields
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, "extra_task"):
                record.extra_task = "-"
            return super().format(record)

    formatter = SafeFormatter(
        "%(asctime)s %(levelname)s %(name)s [task=%(extra_task)s] - %(message)s"
    )

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level.upper())
    console_handler.setFormatter(formatter)

    # --- File handler (with rotation, 5 MB per file, 3 backups) ---
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(level.upper())
    file_handler.setFormatter(formatter)

    # Clear existing handlers (for hot reloads, e.g., in notebooks)
    if root.handlers:
        root.handlers.clear()

    # Add both handlers
    root.addHandler(console_handler)
    root.addHandler(file_handler)

def get_logger(name: str) -> Logger:
    return logging.getLogger(name)
