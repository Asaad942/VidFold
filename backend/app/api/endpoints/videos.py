from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from ...schemas.video import VideoLinkCreate, VideoLinkResponse, Platform, VideoProcessRequest, VideoURL, VideoUpdate
from ...core.database import supabase
from ...utils.url_parser import URLParser
from ...services.visual_analysis import visual_analysis_service
from ...services.audio_transcription import audio_transcription_service
from ...services.auth import auth_service
from ...services.video_management import video_management_service
import uuid
import yt_dlp

router = APIRouter()

@router.post("/", response_model=VideoLinkResponse)
async def add_video(video: VideoLinkCreate):
    """
    Add a new video link to process.
    This endpoint accepts video links from both manual input and app sharing.
    """
    try:
        url = str(video.url)
        
        # If platform is not specified, detect it from the URL
        if video.platform == Platform.UNKNOWN:
            detected_platform = URLParser.detect_platform(url)
            if detected_platform == Platform.UNKNOWN:
                raise HTTPException(
                    status_code=400,
                    detail="Could not detect platform from URL. Please specify the platform."
                )
            video.platform = detected_platform
        
        # Validate URL matches the platform
        if not URLParser.validate_url(url, video.platform):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid URL format for platform {video.platform}"
            )
        
        # Extract video ID
        video_id = URLParser.extract_video_id(url, video.platform)
        if not video_id:
            raise HTTPException(
                status_code=400,
                detail="Could not extract video ID from URL"
            )
        
        # Create the video record in Supabase
        data = {
            "id": str(uuid.uuid4()),
            "url": url,
            "platform": video.platform,
            "title": None,  # Will be updated after processing
            "thumbnail_url": None,  # Will be updated after processing
            "duration": None  # Will be updated after processing
        }
        
        result = supabase.table("videos").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create video")
            
        return VideoLinkResponse(
            id=data["id"],
            url=url,
            platform=video.platform,
            status="processing"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[VideoLinkResponse])
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

@router.post("/process")
async def process_video(
    video: VideoProcessRequest,
    token: str = Depends(auth_service.get_user)
):
    """
    Process a video by extracting metadata, analyzing content, and transcribing audio.
    """
    try:
        # Verify user is authenticated
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # Extract metadata using yt-dlp
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(video.url, download=False)
            
            # Update video with metadata
            metadata = {
                "title": info.get("title"),
                "thumbnail_url": info.get("thumbnail"),
                "duration": info.get("duration")
            }
            
            result = supabase.table("videos").update(metadata).eq("id", video.video_id).execute()
            
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to update video metadata")
            
            # Start visual analysis and transcription in background tasks
            # Note: This should ideally be handled by a proper task queue like Celery
            # For now, we'll do it synchronously
            visual_analysis = await visual_analysis_service.analyze_video(video.url)
            transcription = await audio_transcription_service.transcribe_video(video.url)
            
            # Save analysis results
            analysis_data = {
                "video_id": video.video_id,
                "search_summary": f"{info.get('title')} - {info.get('description')}",
                "visual_summary": str(visual_analysis.get("detected_objects", [])),
                "audio_transcription": transcription.get("text", ""),
                "keywords": visual_analysis.get("detected_objects", []) + transcription.get("keywords", []),
                "metadata": {
                    "visual_analysis": visual_analysis,
                    "transcription": transcription
                }
            }
            
            result = supabase.table("video_analysis").insert(analysis_data).execute()
            
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to save video analysis")
                
            return {"status": "success", "message": "Video processed successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def transcribe_video_audio(
    video: VideoURL,
    token: str = Depends(auth_service.get_user)
) -> Dict[str, Any]:
    """
    Transcribe audio from a video URL using Hugging Face Speech Models.
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