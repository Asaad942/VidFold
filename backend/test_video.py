import asyncio
from app.services.video import video_service

async def test_video_extraction():
    # Test URL (using a public YouTube video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"Testing video metadata extraction for: {test_url}")
    try:
        metadata = await video_service.extract_metadata(test_url)
        print("\n✅ Successfully extracted metadata:")
        print(f"Title: {metadata['title']}")
        print(f"Duration: {metadata['duration']} seconds")
        print(f"Platform: {metadata['platform']}")
        print(f"Thumbnail URL: {metadata['thumbnail_url']}")
        
    except Exception as e:
        print("\n❌ Error extracting metadata:")
        print(str(e))

if __name__ == "__main__":
    asyncio.run(test_video_extraction()) 