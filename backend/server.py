from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import logging
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import app components
from app.core.config import settings
from app.api import auth, videos, search
from app.services.vector_store import vector_store

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

app.include_router(
    videos.router,
    prefix=f"{settings.API_V1_STR}/videos",
    tags=["videos"]
)

app.include_router(search.router, tags=["search"])

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("✅ ffmpeg is available and working")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error running ffmpeg: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ ffmpeg is not installed or not in PATH")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup."""
    # Check ffmpeg availability
    if not check_ffmpeg():
        logger.warning("⚠️ Application may not work correctly without ffmpeg")
    
    # Initialize FAISS vector store
    await vector_store.initialize()
    logger.info("✅ Vector store initialized")

@app.get("/")
async def root():
    return {"message": "Welcome to VidFold API"} 