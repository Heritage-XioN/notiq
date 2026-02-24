import json

import pytest
from celery import Celery, Task
from celery.schedules import crontab
from fakeredis import FakeStrictRedis

from notiq import celery_app, notiq_scheduler, notiq_task, notiq_unscheduler
from notiq.utils.exceptions import SchedulerValidationError, TaskNameRequiredError

from .conftest import SCHEDULER_PARAM_NAMES, SCHEDULER_PARAMS

# ---------------------------------------------------------------------------
# notiq_task tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "task_name, expected",
    [
        ("notiq.test_task_1", "test_1"),
        ("notiq.test_task_2", "test_2"),
        ("notiq.test_task_3", "test_3"),
    ],
)
def test_notiq_task(task_name: str, expected: str):
    # schedule task
    @notiq_task(name=task_name)
    def test_task(self: Task):
        return expected

    # verify decorated function returns the expected data
    assert test_task() == expected


@pytest.mark.parametrize(
    "task_name, x, y, expected",
    [
        ("notiq.test_add_1", 1, 2, 3),
        ("notiq.test_add_2", 2, 3, 5),
        ("notiq.test_add_3", 3, 4, 7),
    ],
)
def test_notiq_task_with_background_task_logic(
    test_app: Celery, task_name: str, x: int, y: int, expected: int
):
    # schedule task
    @notiq_task(name=task_name)
    def add(self: Task, x: int, y: int) -> int:
        return x + y

    # This runs synchronously because of task_always_eager
    result = add.delay(x, y)

    # verify decorated function returns the expected data
    assert result.get() == expected
    # verify if task was successfully created
    assert result.successful()


def test_notiq_task_without_name():
    """Verify TaskNameRequiredError is raised when no name is provided."""
    with pytest.raises(TaskNameRequiredError):

        @notiq_task()
        def unnamed_task(self: Task):  # pyright: ignore[reportUnusedFunction]
            return "should fail"


# ---------------------------------------------------------------------------
# notiq_scheduler tests
# ---------------------------------------------------------------------------


def test_notiq_scheduler():
    # initialise scheduler
    entry = notiq_scheduler(
        name="test.task",
        task="notiq.tasks.send_email",
        schedule=crontab(minute="*/1"),
        args=["test@me.com"],
        kwargs={"subject": "Hi"},
        options={"queue": "priority_queue"},
    ).save()

    # verify all provided configs are correct
    assert entry.name == "test.task"
    assert entry.task == "notiq.tasks.send_email"
    assert entry.schedule == crontab(minute="*/1")
    assert entry.args == ["test@me.com"]
    assert entry.kwargs == {"subject": "Hi"}
    assert entry.options == {"queue": "priority_queue"}
    assert entry.app == celery_app


@pytest.mark.parametrize(SCHEDULER_PARAM_NAMES, SCHEDULER_PARAMS)
def test_notiq_scheduler_save_persists_correct_json_to_redis(
    fake_redis: FakeStrictRedis,
    test_app: Celery,
    task_name: str,
    task: str,
    args: list[str],
    kwargs: dict[str, str],
    schedule: crontab,
    options: dict[str, str],
):
    # initialise scheduler
    entry = notiq_scheduler(
        name=task_name,
        task=task,
        schedule=schedule,
        args=args,
        kwargs=kwargs,
        options=options,
    )

    # Save the entry to Redis
    entry.save()

    # Construct the key RedBeat uses
    redis_key = f"redbeat:{task_name}"

    # Fetch the raw data from our "fake" server
    raw_data = fake_redis.hgetall(redis_key)
    assert raw_data is not None, "Data was not saved to Redis"

    # Decode the JSON stored by RedBeat
    decoded_data = json.loads(raw_data[b"definition"])  # pyright: ignore[reportIndexIssue, reportUnknownArgumentType]

    # Verify the structure matches Celery's expectations
    assert decoded_data["name"] == task_name
    assert decoded_data["task"] == task
    assert decoded_data["args"] == args
    assert decoded_data["kwargs"] == kwargs
    assert decoded_data["options"] == options

    # verify crontab schedule
    assert decoded_data["schedule"]["__type__"] == "crontab"
    assert decoded_data["schedule"]["minute"] == str(list(schedule.minute)[0])
    assert decoded_data["schedule"]["hour"] == str(list(schedule.hour)[0])
    assert decoded_data["schedule"]["day_of_month"] == str(
        list(schedule.day_of_month)[0]
    )
    assert decoded_data["schedule"]["day_of_week"] == str(list(schedule.day_of_week)[0])


# ---------------------------------------------------------------------------
# notiq_unscheduler tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(SCHEDULER_PARAM_NAMES, SCHEDULER_PARAMS)
def test_notiq_unscheduler(
    fake_redis: FakeStrictRedis,
    test_app: Celery,
    task_name: str,
    task: str,
    args: list[str],
    kwargs: dict[str, str],
    schedule: crontab,
    options: dict[str, str],
):
    entry = notiq_scheduler(
        name=task_name,
        task=task,
        schedule=schedule,
        args=args,
        kwargs=kwargs,
        options=options,
    )

    # Save the entry to Redis
    entry.save()

    # Construct the key RedBeat uses
    redis_key = f"redbeat:{task_name}"

    # Fetch the raw data from our "fake" server
    raw_data = fake_redis.hgetall(redis_key)
    # verify data is available
    assert raw_data is not None, "Data was not saved to Redis"

    # unschedule task
    notiq_unscheduler(task_name)
    # Fetch the raw data from our "fake" server
    cleared_raw_data = fake_redis.hgetall(redis_key)
    # assert data is gone
    assert cleared_raw_data == {}


def test_notiq_unscheduler_without_valid_taskname():
    with pytest.raises(SchedulerValidationError):
        notiq_unscheduler("")


# ---------------------------------------------------------------------------
# notiq_scheduler validation tests
# ---------------------------------------------------------------------------


def test_notiq_scheduler_missing_name():
    """Verify SchedulerValidationError when name is missing."""
    with pytest.raises(SchedulerValidationError, match="name is required"):
        notiq_scheduler(
            task="notiq.tasks.send_email",
            schedule=crontab(minute="*/1"),
        )


def test_notiq_scheduler_empty_name():
    """Verify SchedulerValidationError when name is empty/whitespace."""
    with pytest.raises(SchedulerValidationError, match="name is required"):
        notiq_scheduler(
            name="   ",
            task="notiq.tasks.send_email",
            schedule=crontab(minute="*/1"),
        )


def test_notiq_scheduler_missing_task():
    """Verify SchedulerValidationError when task is missing."""
    with pytest.raises(SchedulerValidationError, match="task is required"):
        notiq_scheduler(
            name="test.task",
            schedule=crontab(minute="*/1"),
        )


def test_notiq_scheduler_empty_task():
    """Verify SchedulerValidationError when task is empty/whitespace."""
    with pytest.raises(SchedulerValidationError, match="task is required"):
        notiq_scheduler(
            name="test.task",
            task="   ",
            schedule=crontab(minute="*/1"),
        )


def test_notiq_scheduler_missing_schedule():
    """Verify SchedulerValidationError when schedule is missing."""
    with pytest.raises(SchedulerValidationError, match="schedule is required"):
        notiq_scheduler(
            name="test.task",
            task="notiq.tasks.send_email",
        )
