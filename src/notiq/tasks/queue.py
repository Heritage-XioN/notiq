from collections.abc import Callable
from typing import Any, TypeVar, cast

from celery import shared_task
from celery.app.task import Task

from notiq.utils.exceptions import TaskNameRequiredError

T = TypeVar("T", bound=Callable[..., Any])


def notiq_task(*args: Any, **kwargs: Any) -> Callable[[T], Task]:
    """
    a decorator function to create tasks.
    any function decorated by this is processed by the celery worker.
    the notiq_task decorator is a wrapper around the celery.shared_task decorator.
    it adds some default values for the task. which includes:
    - bind: True
    - retry_backoff: True
    - retry_jitter: True
    - max_retries: 5
    - soft_time_limit: 60
    - time_limit: 75
    - autoretry_for: (ConnectionError, TimeoutError)

    args:
        name: name of task.(should be prefixed with notiq.name_of_task)
        **kwargs: additional arguments to be passed to the celery task

    note:
        the decorated function will receive the task instance as the first argument.
        so the decorated function should accept the task instance as the first argument.
        this is because we set bind=True in the default values. which means pass the value
        of (self: Task) to the decorated function first before any other arguments.

    returns:
        it returns a celery task instance.
        where the celery task commands like .delay
        can be used to execute the decorated function

    Example:
    ```python
        from notiq import notiq_task
        from celery.app.task import Task # this is optional, but recommended for type hinting

        @notiq_task(name="notiq.send_email")
        def send_email(self: Task, to: str, subject: str, body: str) -> None:
            # send email
            pass

        # calling the task
        send_email.delay("[EMAIL_ADDRESS]", "Hello", "This is a test email")


    # you can override any of the default values or add custom values by
    # passing them as arguments to the decorator.
        @notiq_task(name="notiq.send_email", max_retries=3, soft_time_limit=5, time_limit=10)
        def send_email(self: Task, to: str, subject: str, body: str) -> None:
            # send email
            pass
    ```

    Raises:
        TaskNameRequiredError: If no task name is provided via `name` kwarg
            or positional arg.
    """  # noqa: E501
    # custom defaults
    kwargs.setdefault("bind", True)
    kwargs.setdefault("retry_backoff", True)
    kwargs.setdefault("retry_jitter", True)
    kwargs.setdefault("max_retries", 5)
    kwargs.setdefault("soft_time_limit", 60)
    kwargs.setdefault("time_limit", 75)

    # check if the user provided a name for the task
    if "name" not in kwargs and not args:
        # raise task name required error
        raise TaskNameRequiredError("Task name is required")

    default_retry_errors = (ConnectionError, TimeoutError)
    # check if the user passed their own 'autoretry_for'
    if "autoretry_for" in kwargs:
        # if they did, combine the defaults with their custom ones
        # convert to tuple to ensure immutability and compatibility
        kwargs["autoretry_for"] = tuple(
            set(default_retry_errors) | set(kwargs["autoretry_for"])
        )
    else:
        # If they didn't, just use the defaults
        kwargs["autoretry_for"] = default_retry_errors

    return cast(Callable[[T], Task], shared_task(*args, **kwargs))
