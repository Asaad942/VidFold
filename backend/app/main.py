"""
Main entry point for the FastAPI application
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import videos, auth
from .core.tasks import schedule_purge_task
import asyncio

# Add the backend directory to Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

app = FastAPI(title="VidFold API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Welcome to VidFold API"}

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    # Start the purge task
    asyncio.create_task(schedule_purge_task()) 