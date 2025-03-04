from typing import List, Dict, Any
from ..database import supabase
from .vector_store import vector_store
import logging

logger = logging.getLogger(__name__)

class MatchType:
    PERFECT = "PERFECT"
    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"
    LAST_RESORT = "LAST_RESORT"

class SearchService:
    def __init__(self):
        self.db = supabase
        
    async def search_videos(
        self,
        user_id: str,
        query: str,
        platform: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for videos using semantic search and relevance scoring.
        
        Args:
            user_id: ID of the user performing the search
            query: Search query string
            platform: Optional platform filter
            
        Returns:
            List of matching videos with relevance scores (internal match details hidden)
        """
        try:
            # Get query embedding
            query_embedding = await self._get_query_embedding(query)
            
            # Search vector store
            similar_videos = await vector_store.search(query_embedding)
            
            if not similar_videos:
                return []
            
            # Get video details from database
            video_ids = [video_id for video_id, _ in similar_videos]
            
            # Query Supabase for video details
            result = self.db.table("videos").select("*").in_("id", video_ids).eq("user_id", user_id).execute()
            
            if not result.data:
                return []
            
            # Sort videos by similarity score
            video_scores = {video_id: score for video_id, score in similar_videos}
            videos = sorted(
                result.data,
                key=lambda v: video_scores.get(v["id"], 0),
                reverse=True
            )
            
            return videos
            
        except Exception as e:
            logger.error(f"Error in search_videos: {str(e)}")
            return []
        
    async def _get_query_embedding(self, query: str) -> List[float]:
        """
        Get embedding for a search query.
        """
        # TODO: Implement query embedding generation
        # For now, return a dummy embedding
        return [0.0] * 384  # Same dimension as video embeddings
        
    def _calculate_relevance_score(
        self,
        query: str,
        similarity: float,
        title: str,
        search_summary: str,
        visual_summary: str,
        audio_transcription: str,
        keywords: List[str],
        metadata: Dict[str, Any]
    ) -> tuple[float, Dict[str, Any]]:
        """
        Calculate relevance score and match details based on different criteria.
        Internal use only - match details are not exposed to the frontend.
        """
        score = 0.0
        query_lower = query.lower()
        matches = {
            MatchType.PERFECT: False,
            MatchType.STRONG: False,
            MatchType.PARTIAL: False,
            MatchType.WEAK: False,
            MatchType.LAST_RESORT: False
        }
        
        # Perfect match (50 points) - title or search summary
        if query_lower in title.lower() or query_lower in search_summary.lower():
            score += 50
            matches[MatchType.PERFECT] = True
            
        # Strong match - keywords (30 points)
        if any(query_lower in keyword.lower() for keyword in keywords):
            score += 30
            matches[MatchType.STRONG] = True
            
        # Partial match - visual content (20 points)
        if query_lower in visual_summary.lower():
            score += 20
            matches[MatchType.PARTIAL] = True
            
        # Weak match - transcription (10 points)
        if query_lower in audio_transcription.lower():
            score += 10
            matches[MatchType.WEAK] = True
            
        # Last resort - metadata (5 points)
        if metadata and any(
            query_lower in str(value).lower() 
            for value in metadata.values()
        ):
            score += 5
            matches[MatchType.LAST_RESORT] = True
            
        # Vector similarity score (0-20 points)
        similarity_score = 20 * similarity
        score += similarity_score
        
        # Cap the final score at 100
        final_score = min(score, 100.0)
        
        # Return both score and match details (for internal use)
        return final_score, {
            "matches": matches,
            "similarity_score": similarity_score,
            "total_score": final_score
        }

search_service = SearchService() 