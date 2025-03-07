"""
Redis service for caching video metadata
"""
import json
import logging
from typing import Optional, Dict, Any
from redis import Redis
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis = Redis(
                host=os.getenv("REDIS_HOST"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD"),
                ssl=True,
                decode_responses=True
            )
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def get_video_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata from cache
        
        Args:
            url: Video URL
            
        Returns:
            Dict containing video metadata or None if not found
        """
        try:
            key = f"video:metadata:{url}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting video metadata from cache: {str(e)}")
            return None

    def set_video_metadata(self, url: str, metadata: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Cache video metadata
        
        Args:
            url: Video URL
            metadata: Video metadata to cache
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"video:metadata:{url}"
            self.redis.setex(
                key,
                timedelta(seconds=ttl),
                json.dumps(metadata)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching video metadata: {str(e)}")
            return False

    def delete_video_metadata(self, url: str) -> bool:
        """
        Delete video metadata from cache
        
        Args:
            url: Video URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"video:metadata:{url}"
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting video metadata from cache: {str(e)}")
            return False

    def get_processing_status(self, url: str) -> Optional[str]:
        """
        Get video processing status from cache
        
        Args:
            url: Video URL
            
        Returns:
            str: Processing status or None if not found
        """
        try:
            key = f"video:processing:{url}"
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"Error getting processing status from cache: {str(e)}")
            return None

    def set_processing_status(self, url: str, status: str, ttl: int = 3600) -> bool:
        """
        Cache video processing status
        
        Args:
            url: Video URL
            status: Processing status
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"video:processing:{url}"
            self.redis.setex(
                key,
                timedelta(seconds=ttl),
                status
            )
            return True
        except Exception as e:
            logger.error(f"Error caching processing status: {str(e)}")
            return False

    def delete_processing_status(self, url: str) -> bool:
        """
        Delete processing status from cache
        
        Args:
            url: Video URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"video:processing:{url}"
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting processing status from cache: {str(e)}")
            return False

# Initialize Redis service
redis_service = RedisService() 