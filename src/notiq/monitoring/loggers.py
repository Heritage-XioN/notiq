import datetime
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# --- 1. Define the JSON Formatter ---
class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            # Add 'extra' fields if they exist
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


class Logger:
    """
    Creates a custom logger instance that writes to both console and a file.

    Args:
        logger_name (str): The name of the logger (usually __name__).
        log_dir (str): Path to the log directory.
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        Configured logger instance.
    """

    def __init__(
        self,
        logger_name: str,
        log_dir: Path = Path("./logs"),
        level: int = logging.DEBUG,
        file_output: bool = False,
        json_serialize: bool = True,
    ):
        self.logger_name = logger_name
        self.logger: logging.Logger = logging.getLogger(logger_name)
        self.log_dir: Path = log_dir
        self.level: int = level
        self.file_output: bool = file_output
        self.json_serialize: bool = json_serialize

        # --- Create the Logger instance ---
        self.logger.setLevel(self.level)

    def setup(self) -> logging.Logger:
        # --- Prevent Duplicate Handlers (Crucial!) ---
        # If the logger already has handlers, it means it was already set up.
        # We return it immediately to avoid duplicate logs.
        if self.logger.hasHandlers():
            return self.logger

        # --- implement logger handlers ---
        # Console Handler (StreamHandler)
        console_handler = logging.StreamHandler(sys.stdout)
        # Console: simple and readable
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(self.level)
        # Add Console Handler to Logger
        self.logger.addHandler(console_handler)

        # File: detailed (includes file name and line number)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"  # noqa: E501
        )

        if self.file_output:
            # hndles creating log directory if it doesn't exist
            self.log_dir.mkdir(parents=True, exist_ok=True)
            file_output = self.log_dir / f"{self.logger_name}.log"
            # File Handler (RotatingFileHandler)
            # Rotates files so they don't consume infinite disk space.
            # maxBytes=5MB, backupCount=3 (keeps 3 old files)
            file_handler = RotatingFileHandler(
                file_output, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            formatter = JsonFormatter() if self.json_serialize else file_formatter
            file_handler.setFormatter(formatter)
            file_handler.setLevel(self.level)
            # Add File Handler to Logger
            self.logger.addHandler(file_handler)

        # Don't propagate to root logger to avoid double printing if root is configured
        self.logger.propagate = False

        return self.logger
