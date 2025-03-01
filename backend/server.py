import os
import sys
import logging

# Configure logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print current directory and Python path for debugging
current_dir = os.path.dirname(os.path.abspath(__file__))
logger.debug(f"Current directory: {current_dir}")
logger.debug(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
logger.debug(f"sys.path: {sys.path}")

# List all files in current directory for debugging
logger.debug("Files in current directory:")
for item in os.listdir(current_dir):
    logger.debug(f"- {item}")

# List all files in app directory for debugging
app_dir = os.path.join(current_dir, "app")
if os.path.exists(app_dir):
    logger.debug("Files in app directory:")
    for item in os.listdir(app_dir):
        logger.debug(f"- {item}")
else:
    logger.debug("app directory not found!")

# Add the current directory to Python path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    logger.debug(f"Added {current_dir} to sys.path")

try:
    logger.debug("Attempting to import FastAPI...")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    logger.debug("FastAPI imported successfully")

    logger.debug("Attempting to import app components...")
    from app.core.config import settings
    logger.debug("settings imported")
    from app.api import auth, videos, search
    logger.debug("api modules imported")
    from app.services.vector_store import vector_store
    logger.debug("vector_store imported")

    import subprocess

    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    logger.debug("FastAPI app created")

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("CORS middleware configured")

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
    logger.debug("All routers included")

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

    logger.debug("Server setup completed successfully")

except Exception as e:
    logger.error(f"Error during setup: {str(e)}", exc_info=True)
    raise 