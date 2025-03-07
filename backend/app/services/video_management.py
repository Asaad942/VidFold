from typing import Dict, Any, Optional, List
from ..database import supabase
from fastapi import HTTPException
import logging
from datetime import datetime, timedelta
from .vector_store import vector_store

logger = logging.getLogger(__name__)

class VideoManagementService:
    def __init__(self):
        self.supabase = supabase
        self.PURGE_DAYS = 1  # Number of days before permanent deletion

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
            result = self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).is_("deleted_at", "null").execute()
            
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
    ) -> Dict[str, Any]:
        """
        Soft delete a video and its associated data.
        
        Args:
            video_id: ID of the video to delete
            user_id: ID of the user making the deletion
            
        Returns:
            Dictionary containing deletion status and purge deadline
        """
        try:
            # First verify the video exists and belongs to the user
            result = self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).is_("deleted_at", "null").execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="Video not found")
                
            # Calculate purge deadline
            deleted_at = datetime.utcnow()
            purge_deadline = deleted_at + timedelta(days=self.PURGE_DAYS)
                
            # Soft delete the video
            delete_result = self.supabase.table("videos").update({
                "deleted_at": deleted_at.isoformat()
            }).eq("id", video_id).execute()
            
            if delete_result.data:
                # Soft delete associated video analysis
                await self.supabase.table("video_analysis").update({
                    "deleted_at": deleted_at.isoformat()
                }).eq("video_id", video_id).execute()
                
                # Soft delete video categories
                await self.supabase.table("video_categories").update({
                    "deleted_at": deleted_at.isoformat()
                }).eq("video_id", video_id).execute()
                
                # Remove from vector store
                await vector_store.remove_embedding(video_id)
                
            return {
                "success": bool(delete_result.data),
                "deleted_at": deleted_at.isoformat(),
                "purge_deadline": purge_deadline.isoformat(),
                "days_until_purge": self.PURGE_DAYS
            }
            
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def restore_video(
        self,
        video_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Restore a soft-deleted video.
        """
        try:
            # Check if video exists and was deleted
            result = self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).not_.is_("deleted_at", "null").execute()
            
            if not result.data:
                raise HTTPException(status_code=404, detail="Deleted video not found")
                
            # Check if video is past purge deadline
            deleted_at = datetime.fromisoformat(result.data[0]["deleted_at"])
            if datetime.utcnow() - deleted_at > timedelta(days=self.PURGE_DAYS):
                raise HTTPException(status_code=400, detail="Video has been permanently deleted and cannot be restored")
                
            # Restore the video
            restore_result = self.supabase.table("videos").update({
                "deleted_at": None
            }).eq("id", video_id).execute()
            
            if restore_result.data:
                # Restore associated video analysis
                await self.supabase.table("video_analysis").update({
                    "deleted_at": None
                }).eq("video_id", video_id).execute()
                
                # Restore video categories
                await self.supabase.table("video_categories").update({
                    "deleted_at": None
                }).eq("video_id", video_id).execute()
                
                # Rebuild vector store index
                await vector_store.initialize()
                
            return restore_result.data[0]
            
        except Exception as e:
            logger.error(f"Error restoring video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_videos(
        self,
        user_id: str,
        platform: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """
        Get user's videos with optional deleted items.
        
        Args:
            user_id: ID of the user
            platform: Optional platform filter
            limit: Number of videos to return
            offset: Pagination offset
            include_deleted: Include deleted videos
            
        Returns:
            Dictionary containing videos and total count
        """
        try:
            query = self.supabase.table("videos").select("*").eq("user_id", user_id)
            
            if not include_deleted:
                query = query.is_("deleted_at", "null")
                
            if platform:
                query = query.eq("platform", platform)
                
            # Get total count
            count_result = query.count().execute()
            total = count_result.count if hasattr(count_result, 'count') else 0
            
            # Get videos
            videos = query.order("created_at", desc=True).range(offset, offset + limit).execute()
            
            # Process videos to include purge deadline for deleted items
            processed_videos = []
            for v in videos.data:
                video_data = {
                    "id": str(v["id"]),
                    "title": v["title"],
                    "description": v["description"],
                    "url": v["url"],
                    "thumbnail_url": v["thumbnail_url"],
                    "platform": v["platform"],
                    "created_at": v["created_at"].isoformat(),
                    "keywords": v["keywords"] or [],
                    "deleted_at": v.get("deleted_at")
                }
                
                # Add purge deadline information for deleted videos
                if v.get("deleted_at"):
                    deleted_at = datetime.fromisoformat(v["deleted_at"])
                    purge_deadline = deleted_at + timedelta(days=self.PURGE_DAYS)
                    video_data.update({
                        "purge_deadline": purge_deadline.isoformat(),
                        "days_until_purge": max(0, (purge_deadline - datetime.utcnow()).days)
                    })
                
                processed_videos.append(video_data)
            
            return {
                "videos": processed_videos,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Error getting user videos: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _get_video(self, video_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get video details and verify ownership."""
        query = """
            SELECT id, user_id
            FROM videos
            WHERE id = $1 AND user_id = $2
        """
        return await self.supabase.table("videos").select("*").eq("id", video_id).eq("user_id", user_id).execute()

video_management_service = VideoManagementService() 