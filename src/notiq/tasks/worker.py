from celery import Celery


def create_celery_app() -> Celery:
    app = Celery(
        "notiq",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
        include=["notiq.tasks.jobs"],  # prebuilt tasks directory
    )

    # Optional: Configure Celery for better reliability
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # Acknowledge tasks only after completion (prevents data loss if worker crashes)
        task_acks_late=True,
    )

    return app


# The global instance
celery_app = create_celery_app()
