#  Neon-Stdio-Holi-T25/app/config.py

from app.settings import settings
from typing import Dict

class Config:
    """
    Application configuration manager.

    Provides properties for:
    - Database URLs (sync/async)
    - RabbitMQ URL
    - Redis URLs
    - Celery configuration
    - General app settings (CORS, debug, etc.)
    - Webhook, SMS, and OTP configurations
    - Email settings
    """

    # General App Configurations
    @property
    def app_config(self) -> Dict[str, str]:
        return {
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "secret_key": settings.SECRET_KEY,
            "cors_origins": settings.CORS_ORIGINS,
            "dev_mode": settings.DEV_MODE,
        }

    # OTP Expiration Time (should return a Dict[str, int])
    @property
    def otp_expiration_time(self) -> Dict[str, int]:
        return {
            "otp_expiration_time": settings.OTP_EXPIRATION_TIME,
        }

    # Data Storage Expiration Time (should return a Dict[str, int])
    @property
    def data_expiration_time(self) -> Dict[str, int]:
        return {
            "data_expiration_time": settings.DATA_EXPIRATION_TIME,
        }
    
    # Session Expiration Time (should return a Dict[str, int])
    @property
    def session_expiration_time(self) -> Dict[str, int]:
        return {
            "otp_session_expiration_time": settings.OTP_SESSION_EXPIRATION_TIME,
            "user_session": settings.USER_SESSION_EXPIRATION_TIME,
            "main_session": settings.MAIN_SESSION_EXPIRATION_TIME,
            "session": settings.SESSION_EXPIRATION_TIME
        }

    # Database URLs
    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
    
    @property
    def database(self) -> dict:
        return {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
            "db": settings.POSTGRES_DB,
            "role": settings.POSTGRES_ROLE,
            "db_name": settings.POSTGRES_DB_NAME,
            "admin_db_url": settings.ADMIN_DB_URL
        }

    # RabbitMQ URL
    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@"
            f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_VHOST}"
        )

    @property
    def rabbitmq_result_backend(self) -> str:
        return settings.CELERY_RESULT_BACKEND
    
    # Redis URLs
    @property
    def redis_broker_url(self) -> str:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_BROKER}"

    @property
    def redis_result_url(self) -> str:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB_RESULT}"

    # Celery configuration
    @property
    def celery_broker_url(self) -> str:
        return settings.CELERY_BROKER_URL

    @property
    def celery_result_backend(self) -> str:
        return settings.CELERY_RESULT_BACKEND

    # Webhook URL
    @property
    def webhook_url(self) -> str:
        return settings.WEBHOOK_URL
    
    # WebSocket URL
    @property
    def websocket_url(self) -> str:
        return settings.WEBSOCKET_URL

    #  AWS Configuration
    @property
    def aws_credentials(self) -> Dict[str, str]:
        return {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,  # Corrected key name
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,  # Corrected key name
            "aws_region": settings.AWS_REGION  # Corrected key name
        }


    #  AWS SNS Configuration
    @property    
    def aws_sns_topic(self) -> Dict[str, str]:
        return {
            "aws_sns_topic_arn": settings.AWS_SNS_TOPIC_ARN,
            "aws_sns_topic_name": settings.AWS_SNS_TOPIC_NAME
        }
    
    # SMS Service Configuration
    @property
    def sms_api(self) -> Dict[str, str]:
        return {
            "SID": settings.TWILIO_SID,
            "AUTH_TOKEN": settings.TWILIO_AUTH_TOKEN,  # Corrected the key name
            "PHONE_NUMBER": settings.TWILIO_PHONE_NUMBER  # Fixed typo in the key
        }

    # Email Settings
    @property
    def email_address(self) -> str:
        return {
            "address": settings.EMAIL_ADDRESS,
            "password": settings.EMAIL_PASSWORD
        }

    # Razorpay Settings
    @property
    def razorpay_key(self) -> str:
        return {
            "key": settings.RAZORPAY_KEY,
            "secret": settings.RAZORPAY_SECRET
        }
# Export a single Config instance for global access
config = Config()
