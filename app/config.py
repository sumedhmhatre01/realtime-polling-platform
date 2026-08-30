import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not configured. " "Add SECRET_KEY to your .env file."
        )

    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    MAX_POLL_DURATION = int(os.getenv("MAX_POLL_DURATION", "3600"))

    MAX_OPTIONS = int(os.getenv("MAX_OPTIONS", "10"))

    MAX_QUESTION_LENGTH = int(os.getenv("MAX_QUESTION_LENGTH", "500"))

    MAX_OPTION_LENGTH = int(os.getenv("MAX_OPTION_LENGTH", "200"))

    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    if APP_ENV == "production":
        SESSION_COOKIE_SECURE = True
