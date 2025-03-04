import requests
import json
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = "https://ugxvnkdqjrripmjvblsm.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_all_videos():
    try:
        # Query all videos
        result = supabase.table("videos").select("*").execute()
        
        if not result.data:
            print("No videos found in the database.")
            return
            
        print(f"\nFound {len(result.data)} videos in the database:")
        for video in result.data:
            print(f"\nVideo ID: {video.get('id')}")
            print(f"Status: {video.get('status')}")
            print(f"URL: {video.get('url')}")
            print(f"Platform: {video.get('platform')}")
            print(f"Created at: {video.get('created_at')}")
            if video.get('error_message'):
                print(f"Error: {video.get('error_message')}")
            print("-" * 50)
        
    except Exception as e:
        print(f"Error listing videos: {str(e)}")

if __name__ == "__main__":
    list_all_videos() 