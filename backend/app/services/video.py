"""
Video service for handling video operations
"""
import logging
from typing import Dict, Any, Optional
from .browser_service import browser_service
from .redis_service import redis_service
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        """Initialize video service"""
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.instagram_api_key = os.getenv("INSTAGRAM_API_KEY")
        self.tiktok_api_key = os.getenv("TIKTOK_API_KEY")
        self.facebook_api_key = os.getenv("FACEBOOK_API_KEY")

    async def get_video_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get video metadata from cache or platform API
        
        Args:
            url: Video URL
            
        Returns:
            Dict containing video metadata
        """
        try:
            # Check cache first
            cached_metadata = redis_service.get_video_metadata(url)
            if cached_metadata:
                logger.info(f"Retrieved video metadata from cache for URL: {url}")
                return cached_metadata

            # If not in cache, fetch from platform
            platform = self._get_platform(url)
            metadata = await self._fetch_metadata(url, platform)
            
            # Cache the metadata
            if metadata:
                redis_service.set_video_metadata(url, metadata)
            
            return metadata
        except Exception as e:
            logger.error(f"Error getting video metadata: {str(e)}")
            raise

    def _get_platform(self, url: str) -> str:
        """Determine the platform from the URL"""
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "instagram.com" in url:
            return "instagram"
        elif "tiktok.com" in url:
            return "tiktok"
        elif "facebook.com" in url:
            return "facebook"
        else:
            raise ValueError(f"Unsupported platform for URL: {url}")

    async def _fetch_metadata(self, url: str, platform: str) -> Dict[str, Any]:
        """Fetch metadata from the appropriate platform API"""
        try:
            if platform == "youtube":
                return await self._fetch_youtube_metadata(url)
            elif platform == "instagram":
                return await self._fetch_instagram_metadata(url)
            elif platform == "tiktok":
                return await self._fetch_tiktok_metadata(url)
            elif platform == "facebook":
                return await self._fetch_facebook_metadata(url)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
        except Exception as e:
            logger.error(f"Error fetching {platform} metadata: {str(e)}")
            raise

    async def _fetch_youtube_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch metadata from YouTube API"""
        try:
            # Extract video ID from URL
            video_id = self._extract_youtube_id(url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")

            # Use browser service to get metadata
            metadata = await browser_service.get_youtube_metadata(url)
            return metadata
        except Exception as e:
            logger.error(f"Error fetching YouTube metadata: {str(e)}")
            raise

    async def _fetch_instagram_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch metadata from Instagram API"""
        try:
            # Use browser service to get metadata
            metadata = await browser_service.get_instagram_metadata(url)
            return metadata
        except Exception as e:
            logger.error(f"Error fetching Instagram metadata: {str(e)}")
            raise

    async def _fetch_tiktok_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch metadata from TikTok API"""
        try:
            # Use browser service to get metadata
            metadata = await browser_service.get_tiktok_metadata(url)
            return metadata
        except Exception as e:
            logger.error(f"Error fetching TikTok metadata: {str(e)}")
            raise

    async def _fetch_facebook_metadata(self, url: str) -> Dict[str, Any]:
        """Fetch metadata from Facebook API"""
        try:
            # Use browser service to get metadata
            metadata = await browser_service.get_facebook_metadata(url)
            return metadata
        except Exception as e:
            logger.error(f"Error fetching Facebook metadata: {str(e)}")
            raise

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        try:
            if "youtube.com" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be" in url:
                return url.split("/")[-1]
            return None
        except Exception:
            return None

    async def check_processing_status(self, url: str) -> Optional[str]:
        """
        Check if a video is currently being processed
        
        Args:
            url: Video URL
            
        Returns:
            str: Processing status or None if not being processed
        """
        try:
            return redis_service.get_processing_status(url)
        except Exception as e:
            logger.error(f"Error checking processing status: {str(e)}")
            return None

    async def mark_as_processing(self, url: str) -> bool:
        """
        Mark a video as being processed
        
        Args:
            url: Video URL
            
        Returns:
            bool: True if successful
        """
        try:
            return redis_service.set_processing_status(url, "processing")
        except Exception as e:
            logger.error(f"Error marking video as processing: {str(e)}")
            return False

    async def clear_processing_status(self, url: str) -> bool:
        """
        Clear the processing status for a video
        
        Args:
            url: Video URL
            
        Returns:
            bool: True if successful
        """
        try:
            return redis_service.delete_processing_status(url)
        except Exception as e:
            logger.error(f"Error clearing processing status: {str(e)}")
            return False

# Initialize video service
video_service = VideoService() 