from fastapi import APIRouter

from .routes import dep_router, health_router


api_router: APIRouter = APIRouter()
api_router.include_router(dep_router)
api_router.include_router(health_router)
