from typing import Dict, List
import json
from .summary_generator import SearchableSummary
from ..database import get_db
import datetime

async def store_video_analysis(
    video_id: str,
    summary: SearchableSummary
) -> None:
    """
    Store the video analysis data in the database.
    
    Args:
        video_id: UUID of the video
        summary: SearchableSummary object containing all analysis data
    """
    supabase = get_db()
    
    # Create the video_analysis entry
    data = {
        "video_id": video_id,
        "search_summary": summary.search_summary,
        "visual_summary": summary.visual_summary,
        "audio_transcription": summary.raw_data["audio_transcription"],
        "keywords": summary.keywords,
        "metadata": summary.raw_data,
        "confidence_scores": summary.raw_data.get("confidence_scores", {}),
        "processing_status": "completed",
        "embedding": summary.raw_data.get("embedding"),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    result = supabase.table("video_analysis").insert(data).execute()
    return result.data[0] if result.data else None

async def get_video_analysis(
    video_id: str
) -> Dict:
    """
    Retrieve the video analysis data from the database.
    
    Args:
        video_id: UUID of the video
        
    Returns:
        Dict containing all analysis data
    """
    supabase = get_db()
    
    result = supabase.table("video_analysis").select("*").eq("video_id", video_id).execute()
    return result.data[0] if result.data else None

async def update_video_status(
    video_id: str,
    status: str,
    error: str = None
) -> None:
    """
    Update the video processing status.
    
    Args:
        video_id: UUID of the video
        status: New status value
        error: Optional error message
    """
    supabase = get_db()
    
    data = {
        "status": status,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    if error:
        data["error"] = error
    
    supabase.table("videos").update(data).eq("id", video_id).execute() 