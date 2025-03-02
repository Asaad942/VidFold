from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from enum import Enum

class Platform(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    UNKNOWN = "unknown"

class VideoLinkCreate(BaseModel):
    url: HttpUrl
    platform: Optional[Platform] = Field(default=Platform.UNKNOWN)
    
class VideoLinkResponse(BaseModel):
    id: str
    url: str
    platform: Platform
    status: str = "processing"

class VideoURL(BaseModel):
    """Schema for video URL input"""
    url: HttpUrl
    platform: Optional[str] = None
    title: Optional[str] = None

class VideoUpdate(BaseModel):
    """Schema for video update input"""
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None

class VideoResponse(BaseModel):
    """Schema for video response"""
    id: str
    title: str
    description: Optional[str] = None
    url: HttpUrl
    thumbnail_url: Optional[HttpUrl] = None
    platform: str
    keywords: Optional[List[str]] = None 