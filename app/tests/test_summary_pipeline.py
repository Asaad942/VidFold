import yt_dlp
from ..services.summary_generator import generate_searchable_summary

def test_video_pipeline():
    # YouTube video URL
    video_url = "https://youtu.be/7iHxWv3JFAg"
    
    # 1. Extract metadata using yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            metadata = ydl.extract_info(video_url, download=False)
            print("\n✅ Metadata extracted successfully")
            print(f"Title: {metadata.get('title')}")
            print(f"Duration: {metadata.get('duration')} seconds")
            print(f"Description: {metadata.get('description')[:200]}...")
            print(f"Tags: {', '.join(metadata.get('tags', []))}")
        except Exception as e:
            print(f"❌ Error extracting metadata: {str(e)}")
            return

    # 2. Mock visual analysis (in production, this would come from Hugging Face)
    mock_visual_analysis = [
        {
            "objects": ["computer", "desk", "person"],
            "scene": "indoor office",
            "people": ["person wearing glasses"]
        },
        {
            "objects": ["keyboard", "monitor", "coffee cup"],
            "scene": "indoor office",
            "people": ["person typing"]
        }
    ]
    print("\n✅ Visual analysis completed (mock data)")

    # 3. Mock transcription (in production, this would come from Whisper)
    mock_transcription = "This is a test transcription of the video content. In this video, we're demonstrating how our summary generation system works."
    print("✅ Audio transcription completed (mock data)")

    # 4. Generate searchable summary
    try:
        summary = generate_searchable_summary(
            title=metadata.get('title', ''),
            platform="YouTube",
            metadata=metadata,
            visual_analysis=mock_visual_analysis,
            audio_transcription=mock_transcription
        )
        print("\n✅ Summary generated successfully:")
        print(f"\nVisual Summary: {summary.visual_summary}")
        print(f"\nKeywords: {', '.join(summary.keywords)}")
        print(f"\nSearch Summary: {summary.search_summary}")
        
        # Print the full structured data
        print("\n📝 Full Structured Data:")
        print("------------------------")
        print(f"Title: {summary.title}")
        print(f"Platform: {summary.platform}")
        print(f"Visual Summary: {summary.visual_summary}")
        print(f"Audio Summary: {summary.audio_summary}")
        print(f"Number of Keywords: {len(summary.keywords)}")
        print(f"Sample Keywords: {', '.join(summary.keywords[:10])}...")
        
    except Exception as e:
        print(f"❌ Error generating summary: {str(e)}")
        return

if __name__ == "__main__":
    test_video_pipeline() 