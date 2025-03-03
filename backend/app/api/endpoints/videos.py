from fastapi import APIRouter, HTTPException, Depends, Query, Body, BackgroundTasks
from typing import Dict, Any, Optional, List
from ...schemas.video import VideoLinkCreate, VideoLinkResponse, Platform, VideoProcessRequest, VideoURL, VideoUpdate
from ...core.database import supabase
from ...utils.url_parser import URLParser
from ...services.visual_analysis import visual_analysis_service
from ...services.audio_transcription import audio_transcription_service
from ...services.auth import auth_service
from ...services.video_management import video_management_service
from ..auth import get_current_user
import uuid
import yt_dlp
import logging

router = APIRouter()

async def process_video_background(video_id: str, url: str):
    """Background task to process video content"""
    try:
        # Configure yt-dlp with cookies and user agent
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'cookiesfrombrowser': ('chrome',),  # Use Chrome cookies
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'format': 'best',  # Get best quality
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True
        }

        # Get video info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title')
            thumbnail = info.get('thumbnail')
            duration = info.get('duration')

        # Update video record with basic info
        supabase.table("videos").update({
            "title": title,
            "thumbnail_url": thumbnail,
            "duration": duration,
            "status": "processing"
        }).eq("id", video_id).execute()

        # Run visual analysis
        visual_analysis = await visual_analysis_service.analyze_video(url)
        
        # Run audio transcription
        transcription = await audio_transcription_service.transcribe_video(url, video_id)
        
        # Update video record with analysis results
        supabase.table("videos").update({
            "status": "completed",
            "analysis": {
                "visual": visual_analysis,
                "transcription": transcription
            }
        }).eq("id", video_id).execute()

    except Exception as e:
        logging.error(f"Error processing video {video_id}: {str(e)}")
        # Update video record with error status
        try:
            supabase.table("videos").update({
                "status": "error",
                "error": str(e)  # Use 'error' instead of 'error_message'
            }).eq("id", video_id).execute()
        except Exception as db_error:
            logging.error(f"Failed to update error status: {str(db_error)}")

@router.post("/", response_model=VideoLinkResponse)
async def add_video(
    video: VideoLinkCreate,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user)
):
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
            "user_id": user.get("user", {}).get("id"),
            "title": None,  # Will be updated after processing
            "thumbnail_url": None,  # Will be updated after processing
            "duration": None,  # Will be updated after processing
            "status": "pending"  # Initial status
        }
        
        result = supabase.table("videos").insert(data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create video")
            
        # Add background task for video processing
        background_tasks.add_task(process_video_background, data["id"], url)
            
        return VideoLinkResponse(
            id=data["id"],
            url=url,
            platform=video.platform,
            status="pending"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[VideoLinkResponse])
async def get_videos(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all videos for the current user"""
    try:
        # Get user ID from the user object
        user_id = user.get("user", {}).get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Query videos for the user
        result = supabase.table("videos").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            return []
            
        return result.data
    except Exception as e:
        logging.error(f"Error getting videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process a video in two steps:
    1. Extract basic metadata (fast)
    2. Run heavy processing in background (slow)
    """
    try:
        # Step 1: Extract metadata using yt-dlp (fast)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': video.platform.lower() == 'instagram'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                logger.info(f"Attempting to extract info for URL: {video.url}")
                info = ydl.extract_info(video.url, download=False)
                logger.info(f"Successfully extracted info: {info.get('title', 'No title found')}")
                
                # For Instagram, handle the case where title might not be available
                title = info.get('title')
                if not title and video.platform.lower() == 'instagram':
                    title = "Instagram Video"
                
                # Update video with metadata immediately
                metadata = {
                    "title": title,
                    "thumbnail_url": info.get("thumbnail"),
                    "duration": info.get("duration", 0),
                    "status": "processing",  # Indicate background processing is ongoing
                    "description": info.get("description", "")
                }
                
                logger.info(f"Updating video {video.video_id} with metadata: {metadata}")
                
                # Verify the video belongs to the user before updating
                result = supabase.table("videos").select("*").eq("id", video.video_id).eq("user_id", user.get("user", {}).get("id")).execute()
                if not result.data:
                    raise HTTPException(status_code=404, detail="Video not found or access denied")
                
                result = supabase.table("videos").update(metadata).eq("id", video.video_id).execute()
                
                if not result.data:
                    raise HTTPException(status_code=500, detail="Failed to update video metadata")
                
                logger.info(f"Successfully updated video metadata for {video.video_id}")
                
            except Exception as e:
                logger.error(f"Error extracting metadata: {str(e)}")
                # Update with basic metadata if extraction fails
                metadata = {
                    "title": f"Untitled {video.platform} Video",
                    "status": "processing",
                }
                result = supabase.table("videos").update(metadata).eq("id", video.video_id).execute()
        
        # Step 2: Schedule heavy processing for background
        background_tasks.add_task(process_video_background, video.video_id, video.url)
            
        return {
            "status": "processing",
            "message": "Video metadata updated, analysis started in background",
            "metadata": metadata
        }
            
    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}")
        # Update video status to indicate error
        supabase.table("videos").update({"status": "error"}).eq("id", video.video_id).execute()
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