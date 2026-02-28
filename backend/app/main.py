from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import api_router
from .core import init_db, settings, EnvironmentTypes
from .models import Department, Employee


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == EnvironmentTypes.DEVELOPMENT:
        await init_db()
    yield


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(lifespan=lifespan)
    app.include_router(api_router)

    return app
