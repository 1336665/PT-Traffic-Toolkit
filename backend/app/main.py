from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import logging

from app.config import settings
from app.database import init_db, init_sync_db
from app.api import api_router
from app.tasks import scheduler
from app.utils import get_logger
from app.utils.logger import init_db_logging

logger = get_logger('pt_manager.main')

# Track application startup time
APP_START_TIME: datetime = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global APP_START_TIME
    # Startup
    logger.info("Starting PT Manager Pro...")
    APP_START_TIME = datetime.utcnow()
    await init_db()
    # Initialize sync database tables for logger
    init_sync_db()
    # Initialize database logging after DB is ready
    init_db_logging()
    scheduler.start()
    logger.info("PT Manager Pro started successfully")

    yield

    # Shutdown
    scheduler.stop()

    # Close shared HTTP clients to avoid unclosed connection warnings
    try:
        from app.services.speed_limiter import close_http_client
        await close_http_client()
    except Exception:
        pass

    logger.info("PT Manager Pro stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="PT Manager Pro - Full-featured PT management system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - configurable through environment variables
# In production, set CORS_ORIGINS to your frontend domain(s)
cors_origins = settings.cors_origins_list

# Log CORS configuration
if "*" in cors_origins:
    logger.warning("CORS is configured to allow all origins (*). This is not recommended for production.")
else:
    logger.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    uptime_seconds = 0
    if APP_START_TIME:
        uptime_seconds = int((datetime.utcnow() - APP_START_TIME).total_seconds())
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "started_at": APP_START_TIME.isoformat() if APP_START_TIME else None,
        "uptime_seconds": uptime_seconds
    }


# Mount static files for frontend (in production)
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    log_level = "debug" if settings.DEBUG else "info"

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=log_level,
    )
