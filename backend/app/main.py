from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from app.config import settings
from app.database import init_db, init_sync_db
from app.api import api_router
from app.tasks import scheduler
from app.utils import get_logger
from app.utils.logger import init_db_logging

logger = get_logger('pt_manager.main')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PT Manager Pro...")
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
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
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
