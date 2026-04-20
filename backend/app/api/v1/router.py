from fastapi import APIRouter

from app.api.v1 import comparisons, health


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(comparisons.router, prefix="/comparisons", tags=["comparisons"])
