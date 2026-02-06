from pydantic import AmqpDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Notiq configuration with Pydantic validation.

    Can be instantiated in two ways:

    1. Auto-load from environment/.env:
        ```python
        settings = Config()  # Reads NOTIQ_* env vars
        ```

    2. Explicit values (for programmatic use):
        ```python
        settings = Config(
            BROKER_URL="redis://localhost:6379/0",
            RESULT_BACKEND="redis://localhost:6379/0",
            TASK_DIR="./tasks",
        )
        ```

    Environment Variables (with NOTIQ_ prefix):
        NOTIQ_BROKER_URL: Redis or RabbitMQ connection string
        NOTIQ_RESULT_BACKEND: Redis result backend URL
        NOTIQ_TASK_DIR: Directory containing custom task modules (optional)
    """

    model_config = SettingsConfigDict(
        env_prefix="NOTIQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Default to Redis for local dev, but easily swappable for RabbitMQ
    # RabbitMQ URL format: "amqp://user:password@localhost:5672//"
    BROKER_URL: AmqpDsn | RedisDsn | None = None
    RESULT_BACKEND: RedisDsn | None = None
    TASK_DIR: str | None = None
