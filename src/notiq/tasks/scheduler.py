from typing import Any

from celery.schedules import crontab
from redbeat import RedBeatSchedulerEntry

from notiq import Logger
from notiq.tasks.worker import celery_app
from notiq.utils.exceptions import SchedulerValidationError

log = Logger("notiq.tasks.scheduler", json_serialize=False).setup()


def notiq_scheduler(
    name: str | None = None,
    task: str | None = None,
    schedule: crontab | None = None,
    args: Any | None = None,
    kwargs: Any | None = None,
    enabled: bool = True,
    options: Any | None = None,
    **clsargs: Any,
) -> RedBeatSchedulerEntry:
    """
    A factory that returns a configured RedBeat scheduler entry instance.

    Args:
        name: Unique identifier for the scheduled task (e.g., "notiq.send_email").
        task: The task path to be scheduled. Must match a task decorated with
            @notiq_task (e.g., "notiq.tasks.jobs.send_email").
        schedule: Celery schedule object (e.g., crontab(minute=0, hour=0)).
        args: Positional arguments to pass to the task.
        kwargs: Keyword arguments to pass to the task.
        enabled: Whether the scheduled task is enabled. Defaults to True.
        options: Additional Celery task options.
        **clsargs: Additional arguments passed to RedBeatSchedulerEntry.

    Returns:
        RedBeatSchedulerEntry: The configured scheduler entry. Call .save()
            to persist to Redis.

    Raises:
        redis.exceptions.ConnectionError: If Redis is unavailable when saving.

    Example:
        ```python
        from notiq import notiq_scheduler
        from celery.schedules import crontab

        notiq_scheduler(
            name="notiq.send_email",
            task="notiq.send_email",
            schedule=crontab(minute=0, hour=0),
            args=["user@example.com", "Hello", "This is a test email"],
            kwargs={"priority": "high"},
        ).save()
        ```

    How to run the scheduler:
        ```bash
        # start the scheduler worker using uv
        uv run celery -A notiq beat -S redbeat.RedBeatScheduler --loglevel=info
        # start the scheduler worker using celery
        celery -A notiq beat -S redbeat.RedBeatScheduler --loglevel=info
        ```
    """

    # Explicit input validation with helpful messages
    if not name or not name.strip():
        raise SchedulerValidationError(
            "name is required - provide a unique identifier for this scheduled task"
        )
    if not task or not task.strip():
        raise SchedulerValidationError(
            "task is required - provide the task path (e.g., 'notiq.tasks.jobs.my_task')"  # noqa: E501
        )
    if schedule is None:
        raise SchedulerValidationError(
            "schedule is required - provide a crontab schedule object"
        )

    return RedBeatSchedulerEntry(
        name=name,
        task=task,
        schedule=schedule,
        app=celery_app,
        args=args or (),
        kwargs=kwargs or {},
        enabled=enabled,
        options=options or {},
        **clsargs,
    )


def notiq_unscheduler(task_name: str) -> None:
    """
    Delete a scheduled task from Redis.

    Args:
        task_name: The unique name of the scheduled task to delete.

    Raises:
        KeyError: If the task is not found in Redis (logged as warning).
    """
    if not task_name or not task_name.strip():
        raise SchedulerValidationError(
            "task_name is required - provide a unique identifier for this scheduled task"  # noqa: E501
        )
    try:
        entry = RedBeatSchedulerEntry.from_key(f"redbeat:{task_name}", app=celery_app)
        entry.delete()
        log.info("Scheduled task '%s' deleted from Redis.", task_name)
    except KeyError:
        log.warning("Scheduled task '%s' not found in Redis.", task_name)
