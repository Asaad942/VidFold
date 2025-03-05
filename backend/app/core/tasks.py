import asyncio
import logging
from datetime import datetime, timedelta
from app.database import supabase

logger = logging.getLogger(__name__)

async def purge_deleted_videos():
    """Deletes videos that have been soft deleted for more than 1 day."""
    try:
        one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        # Delete videos
        result = supabase.table("videos").delete().lt("deleted_at", one_day_ago).execute()
        
        # Delete associated video analysis
        await supabase.table("video_analysis").delete().lt("deleted_at", one_day_ago).execute()
        
        # Delete associated video categories
        await supabase.table("video_categories").delete().lt("deleted_at", one_day_ago).execute()
        
        logger.info(f"Successfully purged {len(result.data) if result.data else 0} deleted videos")
        
    except Exception as e:
        logger.error(f"Error purging deleted videos: {str(e)}")

async def schedule_purge_task():
    """Schedule the purge task to run daily."""
    while True:
        try:
            # Run purge task
            await purge_deleted_videos()
            
            # Wait for 24 hours before next run
            await asyncio.sleep(24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Error in purge task scheduler: {str(e)}")
            # Wait for 1 hour before retrying on error
            await asyncio.sleep(60 * 60) 