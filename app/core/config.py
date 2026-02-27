from enum import StrEnum

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field


class EnvironmentTypes(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    DB_URL: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/db",
        description="URL для подключения к БД"
    )

    ENVIRONMENT: EnvironmentTypes = Field(
        default=EnvironmentTypes.DEVELOPMENT,
        description="Тип среды разработки"
    )

    @property
    def ASYNC_DB_URL(self) -> str:
        return str(self.DB_URL).replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    class Config:
        env_file = '.env'


settings: Settings = Settings()
