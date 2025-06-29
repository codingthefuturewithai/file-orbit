from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import engine, Base
from app.services.redis_manager import redis_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up CTF Rclone MVP API...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis connection
    await redis_manager.connect()
    
    yield
    
    # Shutdown
    print("Shutting down CTF Rclone MVP API...")
    await redis_manager.disconnect()


app = FastAPI(
    title="CTF Rclone MVP API",
    description="Enterprise file transfer orchestration API built on rclone",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "CTF Rclone MVP API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ctf-rclone-mvp",
        "version": "0.1.0"
    }