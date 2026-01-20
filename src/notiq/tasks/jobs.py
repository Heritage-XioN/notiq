import time
from typing import Any

from celery.app.task import Task

from notiq.monitoring.decorators import monitor
from notiq.tasks.queue import notiq_task


# We reuse your existing tools!
# This task is automatically Monitored AND runs in the background.
@notiq_task(bind=True, name="notiq.send_notification")
@monitor(metric_name="task_send_notification")
def background_notify(self: Task, channel_type: str, message: str) -> str:
    """
    A pre-built background job to send notifications.
    """
    try:
        # notifier = NotificationFactory.get_notifier(channel_type)
        # notifier.send(message)
        return f"Sent via {channel_type}"
    except Exception as exc:
        # Retry logic: Retry in 5s, 10s, 20s... (Exponential Backoff)
        raise self.retry(exc=exc, countdown=5, max_retries=3) from None


@notiq_task(name="notiq.process_analytics")
@monitor(metric_name="task_analytics_aggregation")
def aggregate_analytics(date_str: str) -> dict[str, Any]:
    """
    Simulates a heavy data aggregation job.
    """
    # Imagine this querying a database and crunching numbers
    time.sleep(2)
    return {"date": date_str, "status": "processed", "total_events": 1050}
