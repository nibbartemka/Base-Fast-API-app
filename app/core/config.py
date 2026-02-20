from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, Field


class Settings(BaseSettings):
    DB_URL: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/db",
        description="Database connection URL"
    )

    @property
    def ASYNC_DB_URL(self) -> str:
        return str(self.DB_URL).replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    class Config:
        env_file = '.env'


settings: Settings = Settings()
