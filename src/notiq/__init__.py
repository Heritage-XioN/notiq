# import internal function.
import os

from pydantic import AmqpDsn, RedisDsn, ValidationError

from notiq.config import Config
from notiq.monitoring.builder import MetricBuilder
from notiq.monitoring.decorators import monitor
from notiq.monitoring.loggers import Logger
from notiq.tasks.worker import celery_app
from notiq.utils.dicovery import autodiscover_tasks

# and expose it publicly.
# __all__ defines what happens if someone types "from notiq import *"
__all__ = ["monitor", "MetricBuilder", "celery_app", "Logger", "NotiqConfig", "Config"]

__version__ = "0.0.1"


def _auto_configure_from_env() -> None:
    """
    Auto-configures Celery from environment variables at module import time.

    This enables the worker process to discover tasks without explicit
    NotiqConfig() call. Uses the Config class which provides Pydantic
    validation and automatically loads from .env files.

    Environment Variables (with NOTIQ_ prefix):
        NOTIQ_BROKER_URL: Redis or RabbitMQ broker URL
        NOTIQ_RESULT_BACKEND: Redis result backend URL
        NOTIQ_TASK_DIR: Directory containing custom task modules
    """
    try:
        # Config automatically reads from environment and .env file
        # with NOTIQ_ prefix and validates URLs with Pydantic
        settings = Config()

        if settings.BROKER_URL:
            celery_app.conf.update(broker_url=str(settings.BROKER_URL))

        if settings.RESULT_BACKEND:
            celery_app.conf.update(result_backend=str(settings.RESULT_BACKEND))

        if settings.TASK_DIR:
            modules = autodiscover_tasks(settings.TASK_DIR)
            if modules:
                # Extend existing includes, don't replace
                existing = list(celery_app.conf.get("include", []) or [])  # pyright: ignore[reportUnknownArgumentType]
                celery_app.conf.update(include=existing + modules)

    except ValidationError:
        # If validation fails, silently continue with defaults
        # User will get explicit errors when they call NotiqConfig()
        pass


# Run auto-configuration when the module is imported
_auto_configure_from_env()


def NotiqConfig(
    BROKER_URL: AmqpDsn | RedisDsn,
    RESULT_BACKEND: RedisDsn,
    task_dir: str,
) -> None:
    """
    Configures the Notiq library programmatically.

    This function validates all inputs using Pydantic and configures the
    current process. For production, using a .env file is recommended as
    the worker will automatically load configuration from it.

    Args:
        BROKER_URL: The Redis or RabbitMQ connection string
            (e.g., 'redis://localhost:6379/0').
        RESULT_BACKEND: The Redis connection string for storing task results.
        task_dir: The directory where user tasks are located.

    Note:
        For the Celery worker to auto-discover tasks, create a .env file:

            NOTIQ_BROKER_URL=redis://localhost:6379/0
            NOTIQ_RESULT_BACKEND=redis://localhost:6379/0
            NOTIQ_TASK_DIR=./tasks

    Raises:
        ValueError: If BROKER_URL or RESULT_BACKEND are invalid URLs.
    """
    # Set environment variables for worker processes to pick up
    os.environ["NOTIQ_TASK_DIR"] = str(task_dir)
    os.environ["NOTIQ_BROKER_URL"] = str(BROKER_URL)
    os.environ["NOTIQ_RESULT_BACKEND"] = str(RESULT_BACKEND)

    # Validate using the unified Config class
    try:
        valid_settings = Config(
            BROKER_URL=BROKER_URL,
            RESULT_BACKEND=RESULT_BACKEND,
            TASK_DIR=task_dir,
        )
    except ValidationError as e:
        raise ValueError(f"Invalid configuration provided: {e}") from e

    # Apply broker/backend configuration
    if valid_settings.BROKER_URL:
        celery_app.conf.update(broker_url=str(valid_settings.BROKER_URL))
        print(f"✅ Notiq connected to broker at: {valid_settings.BROKER_URL}")

    if valid_settings.RESULT_BACKEND:
        celery_app.conf.update(result_backend=str(valid_settings.RESULT_BACKEND))

    # Handle task discovery
    if valid_settings.TASK_DIR:
        modules = autodiscover_tasks(valid_settings.TASK_DIR)

        if modules:
            existing = list(celery_app.conf.get("include", []) or [])  # pyright: ignore[reportUnknownArgumentType]
            celery_app.conf.update(include=existing + modules)
            print(
                f"✅ Notiq discovered {len(modules)} task module(s) "
                f"in '{valid_settings.TASK_DIR}'"
            )
        else:
            print(
                f"⚠️ Warning: No python task files found in '{valid_settings.TASK_DIR}'"
            )
