"""Runtime configuration, read from the environment."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "salary"
    reporting_currency: str = "USD"


settings = Settings()
