from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
from .browser_service import browser_service

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        self.browser_service = browser_service

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from a video URL using browser service.
        
        Args:
            url: The video URL to extract metadata from
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            logger.info(f"Starting metadata extraction for URL: {url}")
            
            # Capture frames from the video
            frames = await self.browser_service.capture_video_frames(
                url,
                interval=5,
                max_frames=1  # We only need one frame for metadata
            )
            
            if not frames:
                raise Exception("No frames captured from video")
            
            # Process the metadata
            metadata = {
                'url': url,
                'title': None,  # Will be filled by YouTube API
                'description': None,  # Will be filled by YouTube API
                'thumbnail_url': None,  # Will be filled by YouTube API
                'duration': None,  # Will be filled by YouTube API
                'tags': [],  # Will be filled by YouTube API
                'platform': self._determine_platform(url),
                'created_at': datetime.utcnow().isoformat(),
                'frame_data': frames[0]['frame_data']  # Store first frame for thumbnail
            }
            
            logger.info(f"Processed metadata: {json.dumps(metadata, indent=2)}")
            return metadata
                
        except Exception as e:
            logger.error(f"Error extracting video metadata: {str(e)}", exc_info=True)
            raise Exception(f"Error extracting video metadata: {str(e)}")
    
    def _determine_platform(self, url: str) -> str:
        """Determine the platform from the URL."""
        url = url.lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'facebook.com' in url:
            return 'facebook'
        else:
            return 'unknown'

# Create a singleton instance
video_service = VideoService() 