#  app/settings.py

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Settings:
    """
    Application configuration settings.

    - Loads settings from environment variables with defaults for development.
    - Provides type hints for better code readability and maintainability.
    """

    # General Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("SERVER_IP", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    SECRET_KEY: str = os.getenv("SERVER_IP", "default_secret_key")
    ALLOWED_HOSTS: list[str] = os.getenv("ALLOWED_HOSTS", "*").split(",")
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    DEV_MODE: bool = os.getenv("DEV_MODE", "False").lower() == "true"

    # Database Configuration
    POSTGRES_HOST: str = os.getenv("SERVER_IP", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))

    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("SERVER_IP", "localhost")
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST", "/")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("SERVER_IP", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB_BROKER: int = int(os.getenv("REDIS_DB_BROKER", 0))
    REDIS_DB_RESULT: int = int(os.getenv("REDIS_DB_RESULT", 0))

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL",
        f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}"
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_RESULT}"
    )

    # Websocket Configuration
    WEBSOCKET_URL: str = os.getenv("WEBSOCKET_URL", "ws://${SERVER_IP}:8002/ws")

    # Webhook Configuration
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "http://${SERVER_IP}:8003/webhook/payment")

    # SMS Service Configuration
    TWILIO_SID: str = os.getenv("TWILIO_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "91xxxxxxxxxx")

    # OTP Settings
    OTP_EXPIRATION_TIME: int = int(os.getenv("OTP_EXPIRATION_TIME", 300))

    # Data Storage Settings
    EXPIRATION_TIME: str = os.getenv("EXPIRATION_TIME", "800")

    # Email Configuration
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "your_email_address")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "your_email_password")

# Export an instance of Settings for global access
settings = Settings()