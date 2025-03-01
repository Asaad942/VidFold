import asyncio
import traceback
from app.services.audio_transcription import audio_transcription_service

async def test_transcription():
    # Test with Snapchat video
    test_url = "https://www.snapchat.com/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYZndqbWN2YW5tAZU9a9bfAZU9a7gXAAAAAQ?share_id=UFfyp6mdLPI&locale=ar-AE"
    
    print("Testing audio transcription service...")
    print(f"Using test URL: {test_url}")
    
    try:
        result = await audio_transcription_service.transcribe_video(test_url)
        print("\nTranscription successful!")
        print("Detected language:", result['detected_language'])
        print("\nTranscription text:")
        print(result['transcription'])
        
        # Print chunk information
        if result.get('segments'):
            print("\nSegments with timestamps:")
            for segment in result['segments']:
                # OpenAI segments have start and end as direct attributes
                start = segment.start if hasattr(segment, 'start') else 0
                end = segment.end if hasattr(segment, 'end') else 0
                text = segment.text if hasattr(segment, 'text') else ''
                print(f"[{start:.2f}s - {end:.2f}s] {text}")
        
        return True
    except Exception as e:
        print(f"\nError during transcription: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_transcription())
        if not success:
            exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        traceback.print_exc()
        exit(1) 