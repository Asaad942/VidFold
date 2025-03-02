from typing import Dict, Any, Optional
from ..database.base import get_db
from fastapi import HTTPException
from .vector_store import vector_store

class VideoManagementService:
    def __init__(self):
        self.db = get_db()

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
        # Verify video ownership
        video = await self._get_video(video_id, user_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Build update query
        allowed_fields = {"title", "description", "keywords"}
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        # Update video table
        video_query = """
            UPDATE videos
            SET title = COALESCE($1, title),
                description = COALESCE($2, description)
            WHERE id = $3 AND user_id = $4
            RETURNING id, title, description, url, thumbnail_url, platform
        """
        
        video_result = await self.db.fetch_one(
            video_query,
            updates.get("title"),
            updates.get("description"),
            video_id,
            user_id
        )

        # Update video analysis if keywords changed
        if "keywords" in updates:
            analysis_query = """
                UPDATE video_analysis
                SET keywords = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE video_id = $2
                RETURNING keywords
            """
            await self.db.execute(analysis_query, updates["keywords"], video_id)

        return {
            "id": str(video_result["id"]),
            "title": video_result["title"],
            "description": video_result["description"],
            "url": video_result["url"],
            "thumbnail_url": video_result["thumbnail_url"],
            "platform": video_result["platform"]
        }

    async def delete_video(self, video_id: str, user_id: str) -> bool:
        """
        Delete a video and its associated data.
        
        Args:
            video_id: ID of the video to delete
            user_id: ID of the user making the deletion
            
        Returns:
            True if deletion was successful
        """
        # Verify video ownership
        video = await self._get_video(video_id, user_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Delete video (cascade will handle related records)
        query = """
            DELETE FROM videos
            WHERE id = $1 AND user_id = $2
            RETURNING id
        """
        
        result = await self.db.fetch_one(query, video_id, user_id)
        
        if result:
            # Remove from vector store
            await vector_store.remove_embedding(video_id)
            return True
            
        return False

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
        total = await self.db.fetch_val(count_query, *params)
        
        # Get videos
        videos = await self.db.fetch_all(
            base_query,
            *params,
            limit,
            offset
        )

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
                for v in videos
            ],
            "total": total,
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
        return await self.db.fetch_one(query, video_id, user_id)

video_management_service = VideoManagementService() 