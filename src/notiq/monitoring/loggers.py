import datetime
import json
import logging
import socket
import sys
import threading
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from pathlib import Path

from notiq.monitoring.validation import sanitize_log_filename

# Thread lock for safe handler setup
_setup_lock = threading.Lock()


# --- 1. Define the JSON Formatter ---
class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    Uses UTC timestamps for consistency across distributed systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.UTC
            ).isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            # Contextual data for production observability
            "process_id": record.process,
            "thread_name": record.threadName,
            "hostname": get_cached_system_hostname(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


# maxsize=1 is sufficient since the system hostname rarely changes
@lru_cache(maxsize=1)
def get_cached_system_hostname() -> str:
    """Returns the local system hostname, cached for efficiency."""
    return socket.gethostname()


class Logger:
    """
    Creates a custom logger instance that writes to both console and a file.

    Args:
        logger_name (str): The name of the logger (usually __name__).
        log_dir (Path): Path to the log directory.
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO).
        file_output (bool): Whether to enable file logging.
        json_serialize (bool): Whether to use JSON format for file logs.

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
        """
        Configure logger handlers in a thread-safe manner.
        Idempotent: safe to call multiple times.
        """
        # Thread-safe handler setup to prevent race conditions
        with _setup_lock:
            return self._setup_handlers()

    def _setup_handlers(self) -> logging.Logger:
        """Internal method to configure handlers (called under lock)."""
        # Detect existing handlers to keep setup idempotent
        has_console = any(
            isinstance(h, logging.StreamHandler)
            and not isinstance(h, RotatingFileHandler)
            for h in self.logger.handlers
        )
        has_file = any(isinstance(h, RotatingFileHandler) for h in self.logger.handlers)

        # --- Console Handler ---
        if not has_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(self.level)
            self.logger.addHandler(console_handler)

        # --- File Handler (with error handling) ---
        if self.file_output and not has_file:
            self._setup_file_handler()

        # Don't propagate to root logger to avoid double printing
        self.logger.propagate = False

        return self.logger

    def _setup_file_handler(self) -> None:
        """
        Set up file handler with proper error handling.
        Gracefully degrades if file logging fails.
        """
        try:
            # Create log directory if it doesn't exist
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize filename to prevent path traversal attacks
            safe_filename = sanitize_log_filename(self.logger_name)
            file_path = self.log_dir / f"{safe_filename}.log"

            # File Handler with rotation (5MB, 3 backups)
            file_handler = RotatingFileHandler(
                file_path, maxBytes=5 * 1024 * 1024, backupCount=3
            )

            # Choose formatter based on json_serialize setting
            if self.json_serialize:
                formatter: logging.Formatter = JsonFormatter()
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(filename)s:%(lineno)d - %(message)s"
                )

            file_handler.setFormatter(formatter)
            file_handler.setLevel(self.level)
            self.logger.addHandler(file_handler)

        except PermissionError:
            # Log to stderr but don't crash the application
            sys.stderr.write(
                f"[Logger] Permission denied creating log file for '{self.logger_name}'. "  # noqa: E501
                "File logging disabled.\n"
            )
        except OSError as e:
            # Handles disk full, invalid path, etc.
            sys.stderr.write(
                f"[Logger] Failed to create file handler for '{self.logger_name}': {e}. "  # noqa: E501
                "File logging disabled.\n"
            )
