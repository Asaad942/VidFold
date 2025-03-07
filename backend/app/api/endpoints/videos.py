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
from supabase import create_client
from ...services.browser_service import browser_service
from ...core.database import get_supabase
from ...models.video import VideoCreate, VideoResponse
from ...services.video import video_service
import asyncio

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize YouTube API client
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Initialize Supabase client with service role key for admin operations
admin_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

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
        logging.info(f"Starting video processing for video_id: {video_id}, youtube_id: {youtube_id}")
        
        # Step 1: Get video metadata using YouTube API
        try:
            logging.info("Step 1: Fetching metadata from YouTube API...")
            metadata = await get_video_metadata(youtube_id)
            logging.info("Successfully fetched metadata from YouTube API")
        except Exception as e:
            error_msg = f"Failed to fetch YouTube metadata: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        # Step 2: Update video record with basic info
        try:
            logging.info("Step 2: Updating video record with metadata...")
            admin_supabase.table("videos").update({
                "title": metadata['title'],
                "thumbnail_url": metadata['thumbnail_url'],
                "duration": metadata['duration'],
                "status": "processing",
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }).eq("id", video_id).execute()
            logging.info("Successfully updated video record with metadata")
        except Exception as e:
            error_msg = f"Failed to update video record with metadata: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

        # Step 3: Run visual analysis
        try:
            logging.info("Step 3: Running visual analysis...")
            frames = await browser_service.capture_video_frames(
                url,
                interval=5,
                max_frames=10  # Capture 10 frames for analysis
            )
            
            if not frames:
                raise Exception("No frames captured from video")
            
            analysis_results = await visual_analysis_service.analyze_frames(frames)
            logging.info("Successfully completed visual analysis")
        except Exception as e:
            error_msg = f"Failed to complete visual analysis: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        # Step 4: Run audio transcription
        try:
            logging.info("Step 4: Running audio transcription...")
            transcription = await audio_transcription_service.transcribe_video(url, video_id)
            logging.info("Successfully completed audio transcription")
        except Exception as e:
            error_msg = f"Failed to complete audio transcription: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        # Step 5: Create analysis record
        try:
            logging.info("Step 5: Creating analysis record...")
            analysis_data = {
                "video_id": video_id,
                "visual_summary": analysis_results.get("summary"),
                "audio_transcription": transcription,
                "metadata": metadata,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            
            # Insert analysis data
            admin_supabase.table("video_analysis").insert(analysis_data).execute()
            logging.info("Successfully created analysis record")
        except Exception as e:
            error_msg = f"Failed to create analysis record: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        # Step 6: Update video status to completed
        try:
            logging.info("Step 6: Updating video status to completed...")
            admin_supabase.table("videos").update({
                "status": "completed",
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }).eq("id", video_id).execute()
            logging.info("Successfully completed video processing")
        except Exception as e:
            error_msg = f"Failed to update video status to completed: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error processing video {video_id}: {error_msg}")
        # Update video record with error status
        try:
            admin_supabase.table("videos").update({
                "status": "error",
                "error": error_msg,
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
        
        # Extract user ID from token with better error handling
        user_id = None
        if isinstance(user, dict):
            # Try different possible paths to find user ID
            if "user" in user and isinstance(user["user"], dict):
                user_id = user["user"].get("id")
            elif "id" in user:
                user_id = user["id"]
                
        if not user_id:
            logging.error(f"User ID not found in token structure: {user}")
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        logging.info(f"Using user_id: {user_id}")
        
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
            test_result = admin_supabase.table("videos").select("id").limit(1).execute()
            logging.info(f"Database connection test successful. Found {len(test_result.data)} videos")
        except Exception as e:
            logging.error(f"Database connection test failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Database connection error")
        
        # Try to create the video record using admin client
        try:
            result = admin_supabase.table("videos").insert(data).execute()
            logging.info(f"Insert response: {result}")
            
            if not result.data:
                logging.error(f"Failed to create video record. Supabase response: {result}")
                raise HTTPException(status_code=500, detail="Failed to create video record in database")
                
            # Verify the record was created
            verify_result = admin_supabase.table("videos").select("*").eq("id", record_id).execute()
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
    The video will be permanently deleted after 1 day.
    """
    try:
        result = await video_management_service.delete_video(video_id, user["user"]["id"])
        if not result["success"]:
            raise HTTPException(status_code=404, detail="Video not found")
        return {
            "message": "Video deleted successfully",
            "deleted_at": result["deleted_at"],
            "purge_deadline": result["purge_deadline"],
            "days_until_purge": result["days_until_purge"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{video_id}/restore")
async def restore_video(
    video_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Restore a soft-deleted video.
    Videos can only be restored within 1 day of deletion.
    """
    try:
        video = await video_management_service.restore_video(video_id, user["user"]["id"])
        return {
            "message": "Video restored successfully",
            "video": video
        }
    except HTTPException as e:
        raise e
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

async def process_video(video_id: str, url: str, platform: str, user_id: str):
    """Process a video using frame-based analysis"""
    try:
        # Update video status to processing
        await video_management_service.update_video_status(video_id, "processing")
        
        # Capture frames from the video
        frames = await browser_service.capture_video_frames(
            url,
            interval=5,
            max_frames=10  # Capture 10 frames for analysis
        )
        
        if not frames:
            raise Exception("No frames captured from video")
        
        # Analyze frames
        analysis_results = await visual_analysis_service.analyze_frames(frames)
        
        # Store analysis results
        await video_management_service.store_analysis_results(video_id, analysis_results)
        
        # Update video status to completed
        await video_management_service.update_video_status(video_id, "completed")
        
        logger.info(f"Successfully processed video {video_id}")
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        await video_management_service.update_video_status(video_id, "error", str(e))
        raise 

@router.post("/", response_model=VideoResponse)
async def create_video(
    video: VideoCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Create a new video entry"""
    try:
        # Check if video is already being processed
        processing_status = await video_service.check_processing_status(video.url)
        if processing_status == "processing":
            raise HTTPException(
                status_code=400,
                detail="This video is already being processed"
            )

        # Mark video as processing
        await video_service.mark_as_processing(video.url)

        # Get video metadata (will use cache if available)
        metadata = await video_service.get_video_metadata(video.url)
        
        # Create video entry
        video_data = {
            "user_id": current_user.id,
            "url": video.url,
            "platform": metadata.get("platform"),
            "title": metadata.get("title"),
            "thumbnail_url": metadata.get("thumbnail_url"),
            "duration": metadata.get("duration"),
            "status": "processing"
        }
        
        result = supabase.table("videos").insert(video_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create video entry")
            
        video_id = result.data[0]["id"]
        
        # Start background processing
        background_tasks.add_task(
            process_video,
            video_id,
            video.url,
            current_user.id,
            supabase
        )
        
        return VideoResponse(**result.data[0])
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        await video_service.clear_processing_status(video.url)
        raise HTTPException(status_code=500, detail=str(e))

async def process_video(video_id: str, url: str, user_id: str, supabase: Client):
    """Process video in the background"""
    try:
        # Update video status
        supabase.table("videos").update({"status": "processing"}).eq("id", video_id).execute()
        
        # Capture frames
        frames = await video_service.browser_service.capture_video_frames(
            url,
            interval=5,
            max_frames=10
        )
        
        if not frames:
            raise Exception("No frames captured from video")
            
        # Analyze frames
        analysis_result = await visual_analysis_service.analyze_frames(frames)
        
        # Capture and transcribe audio
        audio_data = await video_service.browser_service.capture_video_audio(url)
        transcription = await audio_transcription_service.transcribe_video(audio_data)
        
        # Store analysis results
        analysis_data = {
            "video_id": video_id,
            "visual_summary": analysis_result.get("summary"),
            "audio_transcription": transcription,
            "metadata": {
                "frame_count": len(frames),
                "duration": frames[-1]["timestamp"] if frames else 0
            }
        }
        
        supabase.table("video_analysis").insert(analysis_data).execute()
        
        # Update video status
        supabase.table("videos").update({"status": "completed"}).eq("id", video_id).execute()
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        supabase.table("videos").update({
            "status": "failed",
            "error": str(e)
        }).eq("id", video_id).execute()
        
    finally:
        # Clear processing status
        await video_service.clear_processing_status(url)

@router.get("/", response_model=List[VideoResponse])
async def get_videos(
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get all videos for the current user"""
    try:
        result = supabase.table("videos").select("*").eq("user_id", current_user.id).execute()
        return [VideoResponse(**video) for video in result.data]
    except Exception as e:
        logger.error(f"Error getting videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get a specific video by ID"""
    try:
        result = supabase.table("videos").select("*").eq("id", video_id).eq("user_id", current_user.id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        return VideoResponse(**result.data[0])
    except Exception as e:
        logger.error(f"Error getting video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str,
    video: VideoUpdate,
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Update a video"""
    try:
        result = supabase.table("videos").update(video.dict(exclude_unset=True)).eq("id", video_id).eq("user_id", current_user.id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        return VideoResponse(**result.data[0])
    except Exception as e:
        logger.error(f"Error updating video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Delete a video"""
    try:
        result = supabase.table("videos").delete().eq("id", video_id).eq("user_id", current_user.id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 