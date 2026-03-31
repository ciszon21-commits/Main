from fastapi import APIRouter
from app.api.v1.endpoints import project, site, analysis

api_router = APIRouter()
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
api_router.include_router(site.router, prefix="/sites", tags=["sites"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
