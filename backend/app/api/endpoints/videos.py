from fastapi import APIRouter, HTTPException
from ...schemas.video import VideoLinkCreate, VideoLinkResponse, Platform
from ...core.database import supabase
from ...utils.url_parser import URLParser
from typing import List
import uuid

router = APIRouter()

@router.post("/videos", response_model=VideoLinkResponse)
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

@router.get("/videos", response_model=List[VideoLinkResponse])
async def list_videos():
    """
    List all videos added by the user.
    """
    try:
        result = supabase.table("videos").select("*").execute()
        
        if not result.data:
            return []
            
        return [
            VideoLinkResponse(
                id=video["id"],
                url=video["url"],
                platform=video["platform"],
                status="completed" if video["title"] else "processing"
            )
            for video in result.data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 