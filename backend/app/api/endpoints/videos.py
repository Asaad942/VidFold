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
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv
import datetime
from ...services.cache_service import cache_service

load_dotenv()

router = APIRouter()

# Initialize YouTube API client
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

async def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """Get video metadata using YouTube Data API with caching"""
    try:
        # Check cache first
        cache_key = cache_service.generate_video_key(video_id)
        cached_data = await cache_service.get(cache_key)
        
        if cached_data:
            logging.info(f"Cache hit for video {video_id}")
            return cached_data
            
        logging.info(f"Cache miss for video {video_id}, fetching from YouTube API")
        
        # If not in cache, fetch from YouTube API
        request = youtube.videos().list(
            part="snippet,contentDetails",
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            raise HTTPException(status_code=404, detail="Video not found")
            
        video_data = response['items'][0]
        snippet = video_data['snippet']
        content_details = video_data['contentDetails']
        
        metadata = {
            'title': snippet['title'],
            'thumbnail_url': snippet['thumbnails']['high']['url'],
            'duration': content_details['duration'],
            'description': snippet.get('description', ''),
            'published_at': snippet['publishedAt']
        }
        
        # Cache the metadata
        await cache_service.set(cache_key, metadata)
        
        return metadata
    except HttpError as e:
        logging.error(f"YouTube API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch video metadata")

async def process_video_background(video_id: str, url: str, youtube_id: str):
    """Background task to process video content"""
    try:
        # Get video metadata using YouTube API
        metadata = await get_video_metadata(youtube_id)
        
        # Update video record with basic info
        supabase.table("videos").update({
            "title": metadata['title'],
            "thumbnail_url": metadata['thumbnail_url'],
            "duration": metadata['duration'],
            "status": "processing",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }).eq("id", video_id).execute()

        # Run visual analysis
        visual_analysis = await visual_analysis_service.analyze_video(url)
        
        # Run audio transcription
        transcription = await audio_transcription_service.transcribe_video(url, video_id)
        
        # Create analysis record
        analysis_data = {
            "video_id": video_id,
            "visual_summary": visual_analysis.get("summary"),
            "audio_transcription": transcription,
            "metadata": metadata,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        # Insert analysis data
        supabase.table("video_analysis").insert(analysis_data).execute()
        
        # Update video status to completed
        supabase.table("videos").update({
            "status": "completed",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }).eq("id", video_id).execute()

    except Exception as e:
        logging.error(f"Error processing video {video_id}: {str(e)}")
        # Update video record with error status
        try:
            supabase.table("videos").update({
                "status": "error",
                "error": str(e),
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
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
        
        # Extract user ID from token
        user_id = user.get("user", {}).get("id")
        if not user_id:
            logging.error(f"User ID not found in token: {user}")
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
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
        
        # Create unique ID for the video record
        record_id = str(uuid.uuid4())
        
        # Create the video record in Supabase
        data = {
            "id": record_id,
            "url": url,
            "platform": video.platform,
            "user_id": user_id,
            "title": None,
            "thumbnail_url": None,
            "duration": None,
            "status": "pending",
            "error": None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        logging.info(f"Attempting to create video record with data: {data}")
        
        # First, verify we can connect to the database
        try:
            test_result = supabase.table("videos").select("id").limit(1).execute()
            logging.info(f"Database connection test successful. Found {len(test_result.data)} videos")
        except Exception as e:
            logging.error(f"Database connection test failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Database connection error")
        
        # Try to create the video record
        try:
            result = supabase.table("videos").insert(data).execute()
            logging.info(f"Insert response: {result}")
            
            if not result.data:
                logging.error(f"Failed to create video record. Supabase response: {result}")
                raise HTTPException(status_code=500, detail="Failed to create video record in database")
                
            # Verify the record was created
            verify_result = supabase.table("videos").select("*").eq("id", record_id).execute()
            if not verify_result.data:
                logging.error(f"Video record not found after creation. ID: {record_id}")
                raise HTTPException(status_code=500, detail="Video record not found after creation")
                
            logging.info(f"Successfully created and verified video record with ID: {record_id}")
                
        except Exception as db_error:
            logging.error(f"Database error creating video: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
            
        # Add background task for video processing
        youtube_id = URLParser.extract_video_id(url, Platform.YOUTUBE)
        background_tasks.add_task(process_video_background, record_id, url, youtube_id)
            
        return VideoLinkResponse(
            id=record_id,
            url=url,
            platform=video.platform,
            status="pending"
        )
    except HTTPException as e:
        logging.error(f"HTTP error in add_video: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error in add_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Soft delete a video and its associated data.
    """
    try:
        success = await video_management_service.delete_video(video_id, user["user"]["id"])
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{video_id}/restore")
async def restore_video(
    video_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Restore a soft-deleted video.
    """
    try:
        video = await video_management_service.restore_video(video_id, user["user"]["id"])
        return video
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_videos(
    user: Dict[str, Any] = Depends(get_current_user),
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False
):
    """
    List user's videos with optional deleted items.
    """
    try:
        return await video_management_service.get_user_videos(
            user["user"]["id"],
            platform=platform,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process")
async def process_video(
    video: VideoProcessRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process a video in two steps:
    1. Extract basic metadata using YouTube API (fast)
    2. Run heavy processing in background (slow)
    """
    try:
        # First, verify the video exists and belongs to the user
        result = supabase.table("videos").select("*").eq("id", video.video_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
            
        db_video = result.data
        if db_video.get("user_id") != user.get("user", {}).get("id"):
            raise HTTPException(status_code=403, detail="Not authorized to process this video")

        # Extract video ID from URL
        youtube_id = URLParser.extract_video_id(video.url, Platform.YOUTUBE)
        if not youtube_id:
            raise ValueError("Invalid YouTube URL")

        # Get video metadata using YouTube API
        metadata = await get_video_metadata(youtube_id)
        
        # Update video with metadata immediately (excluding description)
        update_result = supabase.table("videos").update({
            "title": metadata['title'],
            "thumbnail_url": metadata['thumbnail_url'],
            "duration": metadata['duration'],
            "status": "processing"  # Indicate background processing is ongoing
        }).eq("id", video.video_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update video metadata")
        
        # Schedule heavy processing for background
        background_tasks.add_task(
            process_video_background,
            video.video_id,  # Use the record ID, not the YouTube ID
            video.url,
            youtube_id
        )
            
        return {
            "status": "processing",
            "message": "Video metadata updated, analysis started in background",
            "metadata": metadata
        }
            
    except HTTPException as e:
        # Re-raise HTTP exceptions as is
        raise e
    except Exception as e:
        logging.error(f"Error in process_video: {str(e)}")
        # Update video status to indicate error
        try:
            supabase.table("videos").update({
                "status": "error",
                "error": str(e)
            }).eq("id", video.video_id).execute()
        except Exception as db_error:
            logging.error(f"Failed to update error status: {str(db_error)}")
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