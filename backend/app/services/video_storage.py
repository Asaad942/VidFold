from typing import Dict, List
import json
from .summary_generator import SearchableSummary
from ..database.base import get_db
from sqlalchemy.orm import Session

async def store_video_analysis(
    db: Session,
    video_id: str,
    summary: SearchableSummary
) -> None:
    """
    Store the video analysis data in the database.
    
    Args:
        db: Database session
        video_id: UUID of the video
        summary: SearchableSummary object containing all analysis data
    """
    
    # Create the video_analysis entry
    db.execute(
        """
        INSERT INTO video_analysis (
            video_id,
            search_summary,
            visual_summary,
            audio_transcription,
            keywords,
            metadata
        ) VALUES (
            :video_id,
            :search_summary,
            :visual_summary,
            :audio_transcription,
            :keywords,
            :metadata
        )
        """,
        {
            "video_id": video_id,
            "search_summary": summary.search_summary,
            "visual_summary": summary.visual_summary,
            "audio_transcription": summary.raw_data["audio_transcription"],
            "keywords": summary.keywords,
            "metadata": json.dumps(summary.raw_data)
        }
    )
    
    await db.commit()

async def get_video_analysis(
    db: Session,
    video_id: str
) -> Dict:
    """
    Retrieve the video analysis data from the database.
    
    Args:
        db: Database session
        video_id: UUID of the video
        
    Returns:
        Dict containing all analysis data
    """
    result = await db.execute(
        """
        SELECT * FROM video_analysis
        WHERE video_id = :video_id
        """,
        {"video_id": video_id}
    )
    
    return dict(result.first()) if result.first() else None 