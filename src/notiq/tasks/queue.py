from collections.abc import Callable
from typing import Any, TypeVar, cast

from celery import shared_task
from celery.app.task import Task

T = TypeVar("T", bound=Callable[..., Any])


def notiq_task(*args: Any, **kwargs: Any) -> Callable[[T], Task]:
    # Set custom defaults for your library
    kwargs.setdefault("acks_late", True)
    kwargs.setdefault("reject_on_worker_lost", True)

    # Logic before creating the decorator
    print(f"Creating task with args: {args}")

    return cast(Callable[[T], Task], shared_task(*args, **kwargs))
