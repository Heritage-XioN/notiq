from unittest.mock import patch

import pytest
from celery.schedules import crontab
from fakeredis import FakeStrictRedis

from notiq import celery_app


@pytest.fixture(autouse=True)
def test_app():
    """Configure Celery for synchronous test execution."""
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        redbeat_redis_url="redis://fake",
    )
    return celery_app


@pytest.fixture
def fake_redis():
    """Provide a shared FakeStrictRedis instance for tests."""
    return FakeStrictRedis()


@pytest.fixture(autouse=True)
def mock_redis(fake_redis: FakeStrictRedis):
    """Prevent RedBeat from connecting to a real Redis server."""
    with patch("redbeat.schedulers.get_redis") as mock_get:
        mock_get.return_value = fake_redis
        yield mock_get


# Shared parametrize data for scheduler tests — used by both
# test_notiq_scheduler_save_persists_correct_json_to_redis and test_notiq_unscheduler
SCHEDULER_PARAMS = [
    (
        "notiq.test_add_1",
        "notiq.tasks.send_email",
        ["test@me.com"],
        {"subject": "Hi"},
        crontab(minute="1", hour="10", day_of_month="30", day_of_week="6"),
        {"queue": "priority_queue"},
    ),
    (
        "notiq.test_add_2",
        "notiq.tasks.send_email",
        ["test@me.com"],
        {"subject": "Hi"},
        crontab(minute="1", hour="1", day_of_month="1", day_of_week="1"),
        {"queue": "priority_queue"},
    ),
    (
        "notiq.test_add_3",
        "notiq.tasks.send_email",
        ["test@me.com"],
        {"subject": "Hi"},
        crontab(minute="1", hour="20", day_of_month="2", day_of_week="6"),
        {"queue": "priority_queue"},
    ),
]

SCHEDULER_PARAM_NAMES = "task_name, task, args, kwargs, schedule, options"
