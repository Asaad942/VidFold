from typing import Dict, Any, Optional
from ..database import supabase
from fastapi import HTTPException
import logging
from .vector_store import vector_store

logger = logging.getLogger(__name__)

class VideoManagementService:
    def __init__(self):
        self.supabase = supabase

    async def update_video(
        self,
        video_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update video details.
        
        Args:
            video_id: ID of the video to update
            user_id: ID of the user making the update
            updates: Dictionary of fields to update
            
        Returns:
            Updated video details
        """
        try:
            # First verify the video exists and belongs to the user
            result = self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="Video not found")
                
            # Update the video
            update_result = self.supabase.table("videos").update(updates).eq("id", video_id).execute()
            
            if not update_result.data:
                raise HTTPException(status_code=500, detail="Failed to update video")
                
            return update_result.data[0]
            
        except Exception as e:
            logger.error(f"Error updating video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_video(
        self,
        video_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a video and its associated data.
        
        Args:
            video_id: ID of the video to delete
            user_id: ID of the user making the deletion
            
        Returns:
            True if deletion was successful
        """
        try:
            # First verify the video exists and belongs to the user
            result = self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="Video not found")
                
            # Delete the video (cascade will handle related records)
            delete_result = self.supabase.table("videos").delete().eq("id", video_id).execute()
            
            return bool(delete_result.data)
            
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_videos(
        self,
        user_id: str,
        platform: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get user's saved videos with pagination.
        
        Args:
            user_id: ID of the user
            platform: Optional platform filter
            limit: Number of videos to return
            offset: Pagination offset
            
        Returns:
            Dictionary containing videos and total count
        """
        # Build base query
        base_query = """
            SELECT 
                v.id,
                v.title,
                v.description,
                v.url,
                v.thumbnail_url,
                v.platform,
                v.created_at,
                va.keywords
            FROM videos v
            LEFT JOIN video_analysis va ON v.id = va.video_id
            WHERE v.user_id = $1
        """
        
        count_query = """
            SELECT COUNT(*) 
            FROM videos 
            WHERE user_id = $1
        """
        
        params = [user_id]
        
        if platform:
            base_query += " AND v.platform = $2"
            count_query += " AND platform = $2"
            params.append(platform)

        # Add pagination
        base_query += " ORDER BY v.created_at DESC LIMIT $2 OFFSET $3"
        
        # Get total count
        total = await self.supabase.table("videos").select("*", count="exact").eq("user_id", user_id).execute()
        
        # Get videos
        videos = await self.supabase.table("videos").select("*").eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit).execute()

        return {
            "videos": [
                {
                    "id": str(v["id"]),
                    "title": v["title"],
                    "description": v["description"],
                    "url": v["url"],
                    "thumbnail_url": v["thumbnail_url"],
                    "platform": v["platform"],
                    "created_at": v["created_at"].isoformat(),
                    "keywords": v["keywords"] or []
                }
                for v in videos.data
            ],
            "total": total.data[0]["count"],
            "limit": limit,
            "offset": offset
        }

    async def _get_video(self, video_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get video details and verify ownership."""
        query = """
            SELECT id, user_id
            FROM videos
            WHERE id = $1 AND user_id = $2
        """
        return await self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).execute()

video_management_service = VideoManagementService() 