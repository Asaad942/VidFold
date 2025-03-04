import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

def test_youtube_api():
    try:
        # Get API key
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            print("Error: YOUTUBE_API_KEY not found in environment variables")
            return

        # Create YouTube API client
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Test video ID (Rick Astley - Never Gonna Give You Up)
        video_id = "dQw4w9WgXcQ"

        # Make API request
        request = youtube.videos().list(
            part="snippet,contentDetails",
            id=video_id
        )
        response = request.execute()

        if not response['items']:
            print("Error: Video not found")
            return

        # Print video details
        video_data = response['items'][0]
        snippet = video_data['snippet']
        content_details = video_data['contentDetails']

        print("\nYouTube API Test Results:")
        print("-" * 50)
        print(f"Title: {snippet['title']}")
        print(f"Channel: {snippet['channelTitle']}")
        print(f"Published At: {snippet['publishedAt']}")
        print(f"Duration: {content_details['duration']}")
        print(f"Thumbnail URL: {snippet['thumbnails']['high']['url']}")
        print("-" * 50)
        print("\n✅ YouTube API test successful!")

    except HttpError as e:
        print(f"\n❌ YouTube API Error: {str(e)}")
        if e.resp.status == 403:
            print("This might be due to:")
            print("1. Invalid API key")
            print("2. API key restrictions")
            print("3. Quota exceeded")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")

if __name__ == "__main__":
    test_youtube_api() 