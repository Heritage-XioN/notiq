# import os

from pydantic import ValidationError

from notiq.config import Config
from notiq.monitoring.builder import MetricBuilder
from notiq.monitoring.decorators import monitor
from notiq.monitoring.loggers import Logger
from notiq.tasks.queue import notiq_task
from notiq.tasks.scheduler import notiq_scheduler, notiq_unscheduler
from notiq.tasks.worker import celery_app
from notiq.utils.dicovery import autodiscover_tasks

log = Logger("notiq_config", json_serialize=False).setup()


# __all__ defines what happens if someone types "from notiq import *"
# so all the modules/classes/functions are exposed publicly.
__all__ = [
    "monitor",
    "MetricBuilder",
    "celery_app",
    "Logger",
    "notiq_scheduler",
    "notiq_unscheduler",
    "notiq_task",
]

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

    except ValidationError as e:
        # If validation fails raise exception
        raise ValueError("Invalid configuration provided") from e


# Run auto-configuration when the module is imported
_auto_configure_from_env()

# issue with this. does not work properly
# NOTE: fix programmatic configuration of worker
# def NotiqConfig(
#     BROKER_URL: AmqpDsn | RedisDsn,
#     RESULT_BACKEND: RedisDsn,
#     task_dir: str,
# ) -> None:
#     """
#     Configures the Notiq library programmatically.

#     This function validates all inputs using Pydantic and configures the
#     current process. For production, using a .env file is recommended as
#     the worker will automatically load configuration from it.

#     Args:
#         BROKER_URL: The Redis or RabbitMQ connection string
#             (e.g., 'redis://localhost:6379/0').
#         RESULT_BACKEND: The Redis connection string for storing task results.
#         task_dir: The directory where user tasks are located.

#     Note:
#         For the Celery worker to auto-discover tasks, create a .env file:

#             NOTIQ_BROKER_URL=redis://localhost:6379/0
#             NOTIQ_RESULT_BACKEND=redis://localhost:6379/0
#             NOTIQ_TASK_DIR=./tasks

#     Raises:
#         ValueError: If BROKER_URL or RESULT_BACKEND are invalid URLs.
#     """
#     # Validate using the unified Config class
#     try:
#         valid_settings = Config(
#             BROKER_URL=BROKER_URL,
#             RESULT_BACKEND=RESULT_BACKEND,
#             TASK_DIR=task_dir,
#         )
#     except ValidationError as e:
#         raise ValueError(f"Invalid configuration provided: {e}") from e

#     # Set environment variables for worker processes to pick up
#     os.environ["NOTIQ_TASK_DIR"] = str(valid_settings.TASK_DIR)
#     os.environ["NOTIQ_BROKER_URL"] = str(valid_settings.BROKER_URL)
#     os.environ["NOTIQ_RESULT_BACKEND"] = str(valid_settings.RESULT_BACKEND)

#     # Apply broker/backend configuration
#     if valid_settings.BROKER_URL:
#         celery_app.conf.update(broker_url=str(valid_settings.BROKER_URL))
#         log.info("Notiq connected to broker at: %s", valid_settings.BROKER_URL)

#     if valid_settings.RESULT_BACKEND:
#         celery_app.conf.update(result_backend=str(valid_settings.RESULT_BACKEND))

#     # Handle task discovery
#     if valid_settings.TASK_DIR:
#         modules = autodiscover_tasks(valid_settings.TASK_DIR)

#         if modules:
#             existing = list(celery_app.conf.get("include", []) or [])  # pyright: ignore[reportUnknownArgumentType]  # noqa: E501
#             celery_app.conf.update(include=existing + modules)
#             log.info(
#                 "Notiq discovered %d task module(s) in '%s'",
#                 len(modules),
#                 valid_settings.TASK_DIR,
#             )
#         else:
#             log.warning("No python task files found in '%s'", valid_settings.TASK_DIR)
