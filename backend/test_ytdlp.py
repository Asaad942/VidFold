import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print("Importing yt-dlp...")

import yt_dlp
print("yt-dlp imported successfully")

def test_ytdlp():
    print("\nTesting yt-dlp installation...")
    
    # Test URL (using a public YouTube video)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"Testing URL: {url}")
    
    try:
        # Configure yt-dlp
        ydl_opts = {
            'quiet': False,  # Enable output
            'no_warnings': False,  # Show warnings
            'extract_flat': True,
        }
        
        print("\nInitializing YoutubeDL...")
        # Extract info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Extracting metadata...")
            info = ydl.extract_info(url, download=False)
            
            print("\n✅ Successfully extracted metadata:")
            if info:
                print(f"Title: {info.get('title', 'N/A')}")
                print(f"Duration: {info.get('duration', 'N/A')} seconds")
                print(f"View Count: {info.get('view_count', 'N/A')}")
                print(f"Channel: {info.get('channel', 'N/A')}")
                print(f"Upload Date: {info.get('upload_date', 'N/A')}")
            else:
                print("No metadata was returned")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_ytdlp() 