from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional
from ..services.video import video_service
from ..services.visual_analysis import visual_analysis_service
from ..services.audio_transcription import audio_transcription_service
from ..services.auth import auth_service
from ..services.video_management import video_management_service
from pydantic import BaseModel, HttpUrl

router = APIRouter()

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[list[str]] = None

@router.post("/transcribe")
async def transcribe_video_audio(
    video: VideoURL,
    token: str = Depends(auth_service.get_user)
) -> Dict[str, Any]:
    """
    Transcribe audio from a video URL using Hugging Face Speech Models.
    
    Args:
        video: The video URL to transcribe
        token: JWT token for authentication
        
    Returns:
        Dictionary containing transcription results
    """
    try:
        # Verify user is authenticated
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # Transcribe video audio
        transcription = await audio_transcription_service.transcribe_video(str(video.url))
        return transcription
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_videos(
    platform: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    token: str = Depends(auth_service.get_user)
) -> Dict[str, Any]:
    """
    Get user's saved videos with optional filtering and pagination.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    return await video_management_service.get_user_videos(
        user_id=token["user_id"],
        platform=platform,
        limit=limit,
        offset=offset
    )

@router.put("/{video_id}")
async def update_video(
    video_id: str,
    updates: VideoUpdate,
    token: str = Depends(auth_service.get_user)
) -> Dict[str, Any]:
    """
    Update video details.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    return await video_management_service.update_video(
        video_id=video_id,
        user_id=token["user_id"],
        updates=updates.dict(exclude_unset=True)
    )

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    token: str = Depends(auth_service.get_user)
) -> Dict[str, str]:
    """
    Delete a saved video.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    success = await video_management_service.delete_video(
        video_id=video_id,
        user_id=token["user_id"]
    )
    
    if success:
        return {"message": "Video deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete video") 