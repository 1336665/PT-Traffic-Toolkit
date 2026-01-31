from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.downloaders import router as downloaders_router
from app.api.rss import router as rss_router
from app.api.delete_rules import router as delete_rules_router
from app.api.speed_limit import router as speed_limit_router
from app.api.u2_magic import router as u2_magic_router
from app.api.logs import router as logs_router
from app.api.statistics import router as statistics_router
from app.api.settings import router as settings_router
from app.api.netcup import router as netcup_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(downloaders_router)
api_router.include_router(rss_router)
api_router.include_router(delete_rules_router)
api_router.include_router(speed_limit_router)
api_router.include_router(u2_magic_router)
api_router.include_router(logs_router)
api_router.include_router(statistics_router)
api_router.include_router(settings_router)
api_router.include_router(netcup_router)
