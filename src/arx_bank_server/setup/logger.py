"""Logger module for the application."""

import json
import logging
from logging.config import dictConfig

from .global_settings import settings

LOG_LEVEL: str = settings.LOG_LEVEL

LOGGING_STREAMHANDLER = "logging.StreamHandler"


class JsonFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt, datefmt, style)
        # Set a default date format if not provided
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S"

    def format(self, record):
        record.message = record.getMessage()
        # Ensuring that formatTime is called to set asctime
        record.asctime = self.formatTime(record, self.datefmt)

        # Here, we're using json.dumps to ensure proper JSON encoding of the message
        return json.dumps(
            {
                "timestamp": record.asctime,
                "name": record.name,
                "log_level": record.levelname,
                "message": record.message,
            }
        )


logging_config = {
    "version": 1,  # mandatory field
    # if you want to overwrite existing loggers' configs
    # "disable_existing_loggers": False,
    "formatters": {
        "basic": {
            "()": JsonFormatter,
            "datefmt": "%Y-%m-%d %H:%M:%S",  # Example date format
        },
        "default": {
            "()": JsonFormatter,
            "datefmt": "%Y-%m-%d %H:%M:%S",  # Example date format
        },
        "access": {
            "()": JsonFormatter,
            "datefmt": "%Y-%m-%d %H:%M:%S",  # Example date format
        },
    },
    "handlers": {
        "console": {
            "formatter": "basic",
            "class": LOGGING_STREAMHANDLER,
            "stream": "ext://sys.stderr",
            "level": LOG_LEVEL,
        },
        "default": {
            "formatter": "default",
            "class": LOGGING_STREAMHANDLER,
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": LOGGING_STREAMHANDLER,
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        settings.APP_NAME: {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.error": {
            "level": LOG_LEVEL,
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": LOG_LEVEL,
            "handlers": ["access"],
            "propagate": False,
        },
        "picamera2.picamera2": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
}

dictConfig(logging_config)
logger = logging.getLogger(settings.APP_NAME)
