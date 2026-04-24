from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.database import init_db
from app.api.routes import auth, learning, courses, tutor, agents
from app.core.redis_client import init_redis, close_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Learning Platform")
    await init_db()
    await init_redis()
    yield
    # Shutdown
    logger.info("Shutting down AI Learning Platform")
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Learning Platform with Agent System",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(learning.router, prefix="/api/learning", tags=["Learning"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(tutor.router, prefix="/api/tutor", tags=["AI Tutor"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
