import tzlocal
from celery import Celery


def create_celery_app() -> Celery:
    """
    a factory that returns the configured celery app instance
    with the following configurations:
    - broker: redis://localhost:6379/0 # defaults broker url
    - backend: redis://localhost:6379/0 # defaults backend url
    - timezone: local_tz
    - enable_utc: True
    - task_time_limit: 3600
    - task_soft_time_limit: 3300
    - broker_heartbeat: 120
    - broker_connection_timeout: 30
    - broker_pool_limit: 30
    - task_acks_late: True
    - task_reject_on_worker_lost: True
    - task_ignore_result: False
    - worker_prefetch_multiplier: 1
    - worker_concurrency: 10
    - worker_max_tasks_per_child: 1000
    - worker_max_memory_per_child: 1000000
    - worker_disable_rate_limit: False
    - result_expires=86400

    config:
        to configure the broker, backend, task_dir, etc
        pass the config as arguments to the NotiqConfig class
        or to as an environment variables prefixed with NOTIQ_

        Example:
        ```python
        from notiq import NotiqConfig
        from pydantic import AmqpDsn, RedisDsn

        # using redis as broker and backend
        NotiqConfig(
            BROKER_URL=RedisDsn("redis://localhost:6379/0"),
            RESULT_BACKEND=RedisDsn("redis://localhost:6379/0"),
            task_dir="./example",
        )

        # using rabbitmq as broker and redis as backend
        NotiqConfig(
            BROKER_URL=AmqpDsn("amqp://guest:guest@localhost:5672//"),
            RESULT_BACKEND=RedisDsn("redis://localhost:6379/0"),
            task_dir="./example",
        )
        ```

        or using environment variables in a .env file or in the terminal:
        ```bash
        export NOTIQ_BROKER_URL="redis://localhost:6379/0"
        export NOTIQ_RESULT_BACKEND="redis://localhost:6379/0"
        export NOTIQ_TASK_DIR="./example"
        ```


    Returns:
        Celery: The configured celery app instance

    usage:
        ```bash
        # start the worker using uv
        uv run celery -A notiq worker --loglevel=info
        # start the worker using celery
        celery -A notiq worker --loglevel=info

        # for windows
        # start the worker using uv
        uv run celery -A notiq worker --loglevel=info --pool=solo
        # start the worker using celery
        celery -A notiq worker --loglevel=info --pool=solo
        ```
    """  # noqa: E501
    app = Celery(
        "notiq",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
        include=["notiq.tasks.jobs"],  # prebuilt tasks directory
    )
    # gets timezone info of the host machine
    local_tz = tzlocal.get_localzone_name()

    # Configuration to ensure celery reliability
    app.conf.update(
        # Task scheduler
        redbeat_redis_url="redis://localhost:6379/1",
        # Task settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=local_tz,
        enable_utc=True,
        # Time limits
        task_time_limit=3600,
        task_soft_time_limit=3300,
        # long running task optimization
        broker_heartbeat=120,
        broker_connection_timeout=30,
        broker_pool_limit=30,
        # Task acknowledgement
        task_acks_late=True,  # Ack tasks only after completion (prevents data loss if worker crashes)  # noqa: E501
        task_reject_on_worker_lost=True,  # Reject tasks if worker crashes (prevents data loss if worker crashes)  # noqa: E501
        task_ignore_result=False,
        # Worker settings
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_max_memory_per_child=1000000,
        worker_disable_rate_limit=False,
        result_expires=86400,
    )

    return app


# The global instance
celery_app = create_celery_app()
