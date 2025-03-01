from typing import List, Dict, Any
import numpy as np
from ..database import get_db
from ..utils.embeddings import get_embedding
from .vector_store import vector_store

class MatchType:
    PERFECT = "PERFECT"
    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"
    LAST_RESORT = "LAST_RESORT"

class SearchService:
    def __init__(self):
        self.db = get_db()
        
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
        # Get query embedding
        query_embedding = get_embedding(query)
        
        # Get similar videos from FAISS
        similar_videos = await vector_store.search(query_embedding)
        
        if not similar_videos:
            return []
            
        # Build video IDs list and similarity score map
        video_ids = [vid_id for vid_id, _ in similar_videos]
        similarity_scores = {vid_id: score for vid_id, score in similar_videos}
        
        # Build base query
        base_query = """
            SELECT 
                v.id,
                v.title,
                v.url,
                v.thumbnail_url,
                v.platform,
                va.search_summary,
                va.visual_summary,
                va.audio_transcription,
                va.keywords,
                va.metadata
            FROM videos v
            JOIN video_analysis va ON v.id = va.video_id
            WHERE v.user_id = $1
            AND v.id = ANY($2)
        """
        
        params = [user_id, video_ids]
        
        if platform:
            base_query += " AND v.platform = $3"
            params.append(platform)
            
        # Execute search query
        results = await self.db.fetch_all(base_query, *params)
        
        # Calculate relevance scores and determine match types
        scored_results = []
        for result in results:
            video_id = str(result["id"])
            similarity = similarity_scores.get(video_id, 0.0)
            
            # Calculate score and get match details
            score, match_details = self._calculate_relevance_score(
                query=query,
                similarity=similarity,
                title=result["title"],
                search_summary=result["search_summary"],
                visual_summary=result["visual_summary"],
                audio_transcription=result["audio_transcription"],
                keywords=result["keywords"],
                metadata=result.get("metadata", {})
            )
            
            # Create the result object (excluding internal match details)
            scored_results.append({
                "id": video_id,
                "title": result["title"],
                "url": result["url"],
                "thumbnail_url": result["thumbnail_url"],
                "platform": result["platform"],
                "relevance_score": score
            })
            
        # Sort by relevance score
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_results
        
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