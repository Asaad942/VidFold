import asyncio
import logging
from datetime import datetime, timedelta
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Supabase client with service role key
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

async def purge_deleted_videos():
    """Purge videos that have been soft deleted for more than 1 day"""
    try:
        # Calculate the cutoff date (1 day ago)
        cutoff_date = datetime.utcnow() - timedelta(days=1)
        
        # Find videos that have been soft deleted for more than 1 day
        result = supabase.table("videos").select("id").eq("status", "deleted").lt("deleted_at", cutoff_date.isoformat()).execute()
        
        if not result.data:
            logger.info("No videos to purge")
            return
            
        # Get the video IDs to purge
        video_ids = [video["id"] for video in result.data]
        
        # Delete the videos and their associated data
        # The ON DELETE CASCADE will handle the related records
        delete_result = supabase.table("videos").delete().in_("id", video_ids).execute()
        
        logger.info(f"Successfully purged {len(video_ids)} deleted videos")
        
    except Exception as e:
        logger.error(f"Error purging deleted videos: {str(e)}")
        raise

async def run_periodic_tasks():
    """Run periodic maintenance tasks"""
    while True:
        try:
            # Purge deleted videos
            await purge_deleted_videos()
            
            # Wait for 1 hour before running again
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in periodic tasks: {str(e)}")
            # Wait for 5 minutes before retrying on error
            await asyncio.sleep(300) 