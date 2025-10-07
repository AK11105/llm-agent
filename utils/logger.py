import logging
import sys
from logging import Logger

def configure_logging(level: str = "INFO") -> None:
    """
    Configure a small but structured logger used across the project.
    Adjust or extend with handlers (file/JSON) as needed later.
    """
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [task=%(extra_task)s] - %(message)s"
    )

    # Wrap formatter to be tolerant if extra keys aren't provided
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, "extra_task"):
                record.extra_task = "-"
            return super().format(record)

    handler.setFormatter(SafeFormatter("%(asctime)s %(levelname)s %(name)s [task=%(extra_task)s] - %(message)s"))
    # Clear existing handlers to avoid duplicate logs in reloads
    if root.handlers:
        root.handlers = []
    root.addHandler(handler)

def get_logger(name: str) -> Logger:
    return logging.getLogger(name)
