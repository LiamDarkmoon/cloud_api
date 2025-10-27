from pydantic_settings import BaseSettings


class settings(BaseSettings):
    # Database
    DB_URL: str
    DB_KEY: str
    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"


config = settings()
