from fastapi import APIRouter

from app.api.api_v1.endpoints import jobs, transfers, endpoints, transfer_templates, stats, logs, settings

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(endpoints.router, prefix="/endpoints", tags=["endpoints"])
api_router.include_router(transfer_templates.router, prefix="/transfer-templates", tags=["transfer-templates"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])