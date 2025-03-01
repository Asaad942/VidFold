from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
from pydantic import BaseModel
from ..services.auth import auth_service
from ..services.search import search_service

router = APIRouter()

class SearchResponse(BaseModel):
    id: str
    title: str
    url: str
    thumbnail_url: str
    platform: str
    relevance_score: float

@router.get("/videos/search", response_model=List[SearchResponse])
async def search_videos(
    query: str = Query(..., min_length=1),
    platform: str = Query(None),
    token: str = Depends(auth_service.get_user)
) -> List[Dict[str, Any]]:
    """
    Search for videos using natural language query.
    
    Args:
        query: Search query string
        platform: Optional platform filter (YouTube, Instagram, etc.)
        token: JWT token for authentication
        
    Returns:
        List of matching videos with relevance scores
    """
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        results = await search_service.search_videos(
            user_id=token["user_id"],
            query=query,
            platform=platform
        )
        return results
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 