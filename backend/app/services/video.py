from typing import Dict, Any, Optional
import yt_dlp
from datetime import datetime
import json

class VideoService:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from a video URL using yt-dlp.
        
        Args:
            url: The video URL to extract metadata from
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                # Process the metadata
                metadata = {
                    'url': url,
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'thumbnail_url': self._get_best_thumbnail(info),
                    'duration': info.get('duration'),
                    'tags': info.get('tags', []),
                    'platform': self._determine_platform(url),
                    'created_at': datetime.utcnow().isoformat(),
                    'raw_metadata': json.dumps(info)  # Store full metadata for future use
                }
                
                return metadata
                
        except Exception as e:
            raise Exception(f"Error extracting video metadata: {str(e)}")
    
    def _get_best_thumbnail(self, info: Dict[str, Any]) -> Optional[str]:
        """Get the best quality thumbnail URL from the video info."""
        if not info:
            return None
            
        # Try to get the best thumbnail
        if 'thumbnails' in info and info['thumbnails']:
            # Sort thumbnails by resolution (if available)
            thumbnails = sorted(
                info['thumbnails'],
                key=lambda x: x.get('height', 0) * x.get('width', 0),
                reverse=True
            )
            return thumbnails[0].get('url')
            
        # Fallback to thumbnail if available
        return info.get('thumbnail')
    
    def _determine_platform(self, url: str) -> str:
        """Determine the platform from the video URL."""
        url = url.lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'facebook'
        else:
            return 'other'

# Initialize the video service
video_service = VideoService() 