from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
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