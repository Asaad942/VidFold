import requests
import json
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials. Please check your .env file.")

print(f"Using Supabase URL: {SUPABASE_URL}")
# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_auth_tokens():
    # Credentials
    credentials = {
        "username": "testuser@example.com",
        "password": "testpassword123"
    }
    
    # Login to get tokens
    login_response = requests.post(
        "https://vidfold-backend.onrender.com/api/v1/auth/login",
        data=credentials
    )
    login_response.raise_for_status()
    token_data = login_response.json()
    return token_data.get("access_token"), token_data.get("refresh_token")

def check_video_status(video_id):
    try:
        # Query the video status
        result = supabase.table("videos").select("*").eq("id", video_id).execute()
        
        if not result.data:
            print(f"No video found with ID: {video_id}")
            return
            
        video = result.data[0]
        print("\nVideo Status:")
        print(json.dumps(video, indent=2))
        
        if video.get("status") == "error":
            print(f"\nError processing video: {video.get('error')}")
        elif video.get("status") == "completed":
            print("\nVideo processing completed successfully!")
        elif video.get("status") == "processing":
            print("\nVideo is currently being processed...")
        else:
            print("\nVideo is pending processing. The background task should start soon.")
            
    except Exception as e:
        print(f"Error checking video status: {str(e)}")

if __name__ == "__main__":
    # Use the video ID from the most recent upload
    VIDEO_ID = "82391cc1-bae7-42d6-ae45-560b853ed5a2"
    check_video_status(VIDEO_ID) 