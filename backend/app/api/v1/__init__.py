from fastapi import APIRouter

from app.api.v1.routers import (
    admin,
    auth,
    dashboard,
    deadlines,
    opportunities,
    profile,
    saved,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(opportunities.router)
api_router.include_router(opportunities.organizations_router)
api_router.include_router(opportunities.categories_router)
api_router.include_router(dashboard.router)
api_router.include_router(saved.router)
api_router.include_router(deadlines.router)
api_router.include_router(profile.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
