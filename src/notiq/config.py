# from pydantic_settings import BaseSettings, SettingsConfigDict


# # sets up config for accessing env variables
# class NotiqConfig(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env")

#     # Default to Redis for local dev, but easily swappable for RabbitMQ
#     # RabbitMQ URL format: "amqp://user:password@localhost:5672//"
#     BROKER_URL: str = os.getenv("NOTIQ_BROKER_URL", "redis://localhost:6379/0")
#     RESULT_BACKEND: str = os.getenv("NOTIQ_RESULT_BACKEND", "redis://localhost:6379/0")


# settings = NotiqConfig()

import os
from dataclasses import dataclass


@dataclass
class NotiqConfig:
    # Default to Redis for local dev, but easily swappable for RabbitMQ
    # RabbitMQ URL format: "amqp://user:password@localhost:5672//"
    BROKER_URL: str = os.getenv("NOTIQ_BROKER_URL", "redis://localhost:6379/0")
    RESULT_BACKEND: str = os.getenv("NOTIQ_RESULT_BACKEND", "redis://localhost:6379/0")


settings = NotiqConfig()
