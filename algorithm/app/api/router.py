from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.internal import router as internal_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(internal_router)
