from typing import Dict, List, Optional
import json
from pydantic import BaseModel

class VideoAnalysisData(BaseModel):
    title: str
    platform: str
    metadata: Dict
    visual_analysis: List[Dict]
    audio_transcription: str
    
class SearchableSummary(BaseModel):
    title: str
    platform: str
    visual_summary: str
    audio_summary: str
    keywords: List[str]
    search_summary: str
    raw_data: Dict  # Stores all original data for future reference

def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text while removing common words."""
    # TODO: Implement more sophisticated keyword extraction
    # For now, just split and lowercase unique words
    words = set(word.lower() for word in text.split())
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
    return list(words - common_words)

def generate_visual_summary(visual_analysis: List[Dict]) -> str:
    """Generate a human-readable summary from visual analysis results."""
    summary_parts = []
    
    # Collect unique objects and scenes
    objects = set()
    scenes = set()
    people = set()
    
    for frame in visual_analysis:
        if 'objects' in frame:
            objects.update(frame['objects'])
        if 'scene' in frame:
            scenes.add(frame['scene'])
        if 'people' in frame:
            people.update(frame['people'])
    
    if people:
        summary_parts.append(f"Shows {', '.join(people)}")
    if objects:
        summary_parts.append(f"Contains {', '.join(objects)}")
    if scenes:
        summary_parts.append(f"Set in {', '.join(scenes)}")
    
    return '. '.join(summary_parts)

def generate_searchable_summary(
    title: str,
    platform: str,
    metadata: Dict,
    visual_analysis: List[Dict],
    audio_transcription: str
) -> SearchableSummary:
    """
    Generate a comprehensive searchable summary combining all video analysis data.
    
    Args:
        title: Video title
        platform: Platform where the video is from (YouTube, Instagram, etc.)
        metadata: Raw metadata from yt-dlp
        visual_analysis: List of visual analysis results from Hugging Face
        audio_transcription: Full audio transcription from Whisper
    
    Returns:
        SearchableSummary object containing organized and searchable information
    """
    
    # Generate visual summary
    visual_summary = generate_visual_summary(visual_analysis)
    
    # Create a condensed audio summary (first 200 characters for quick reference)
    audio_summary = audio_transcription[:200] + "..." if len(audio_transcription) > 200 else audio_transcription
    
    # Collect keywords from all sources
    keywords = set()
    
    # Add keywords from title
    keywords.update(extract_keywords(title))
    
    # Add keywords from metadata
    if 'tags' in metadata:
        keywords.update(metadata['tags'])
    if 'description' in metadata:
        keywords.update(extract_keywords(metadata['description']))
    
    # Add keywords from visual analysis
    for frame in visual_analysis:
        if 'objects' in frame:
            keywords.update(frame['objects'])
        if 'scene' in frame:
            keywords.add(frame['scene'])
    
    # Add keywords from transcription
    keywords.update(extract_keywords(audio_transcription))
    
    # Create a comprehensive search summary
    search_summary = f"{title}. {visual_summary}. {audio_summary}"
    
    # Store all raw data for future reference
    raw_data = {
        "metadata": metadata,
        "visual_analysis": visual_analysis,
        "audio_transcription": audio_transcription
    }
    
    return SearchableSummary(
        title=title,
        platform=platform,
        visual_summary=visual_summary,
        audio_summary=audio_summary,
        keywords=list(keywords),
        search_summary=search_summary,
        raw_data=raw_data
    ) 