from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class settings(BaseSettings):
    # Database
    DB_URL: str
    DB_KEY: str
    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    model_config = (
        SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
        if os.getenv("VERCEL") is None
        else SettingsConfigDict()
    )


config = settings()
