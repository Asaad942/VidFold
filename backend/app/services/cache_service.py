import redis
import json
import os
from dotenv import load_dotenv
from typing import Optional, Any
import logging

load_dotenv()

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('UPSTASH_REDIS_HOST'),
            port=int(os.getenv('UPSTASH_REDIS_PORT', 6379)),
            password=os.getenv('UPSTASH_REDIS_PASSWORD'),
            ssl=True,
            decode_responses=True
        )
        self.default_ttl = 86400  # 24 hours in seconds

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        """
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logging.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache with optional TTL
        """
        try:
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logging.error(f"Cache set error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        """
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logging.error(f"Cache delete error: {str(e)}")
            return False

    def generate_video_key(self, video_id: str, platform: str = 'youtube') -> str:
        """
        Generate a cache key for video metadata
        """
        return f"video_metadata:{platform}:{video_id}"

# Initialize cache service
cache_service = CacheService() 