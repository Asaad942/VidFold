from typing import Dict, Any, Optional
import yt_dlp
from datetime import datetime
import json
import random
import asyncio

class VideoService:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'format': 'best',
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True,
            'extract_flat': True,
            'format': 'best',
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 10,
            'extractor_retries': 10,
            'retry_sleep': 5,
            'retry_sleep_functions': {'fragment': lambda n: 5 * (n + 1)},
            'sleep_interval': 5,
            'max_sleep_interval': 30,
            'sleep_interval_requests': 3,
            'throttledratelimit': 100000,
            'ratelimit': 100000,
            'concurrent_fragments': 1,
            'buffersize': 32768,
            'http_chunk_size': 10485760,
            'retry_sleep_functions': {'fragment': lambda n: 5 * (n + 1)},
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['js', 'configs', 'webpage']
                }
            }
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
            # Add random delay to avoid rate limiting
            await asyncio.sleep(random.uniform(1, 3))
            
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