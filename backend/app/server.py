import os
import sys
import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Configure logging first
logging.basicConfig(level=logging.INFO)  # Change to INFO level
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

# Add the parent directory to Python path
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    logger.debug(f"Added {parent_dir} to sys.path")

try:
    logger.debug("Attempting to import FastAPI...")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    logger.debug("FastAPI imported successfully")

    logger.debug("Attempting to import app components...")
    from core.config import settings
    logger.debug("settings imported")
    from api import auth, search
    from api.endpoints import videos  # Updated import path
    logger.debug("api modules imported")
    from services.vector_store import vector_store
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
        allow_origins=["*"],  # In production, replace with your frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    logger.debug("CORS middleware configured")

    # Include routers
    app.include_router(
        auth.router,
        prefix=f"{settings.API_V1_STR}/auth",
        tags=["authentication"]
    )

    app.include_router(
        videos.router,  # Using the correct videos router
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
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"❌ ffmpeg error: {e}")
            return False

    async def initialize_vector_store():
        """Initialize the vector store in the background."""
        try:
            await vector_store.initialize()
            logger.info("✅ Vector store initialized")
        except Exception as e:
            logger.error(f"❌ Vector store initialization error: {e}")

    @app.on_event("startup")
    async def startup_event():
        """Initialize services on app startup."""
        check_ffmpeg()
        # Start vector store initialization in the background
        background_tasks = BackgroundTasks()
        background_tasks.add_task(initialize_vector_store)

    @app.get("/")
    async def root():
        """Quick health check endpoint."""
        return {"status": "healthy", "message": "Welcome to VidFold API"}

    logger.debug("Server setup completed successfully")

except Exception as e:
    logger.error(f"Error during setup: {str(e)}", exc_info=True)
    raise 