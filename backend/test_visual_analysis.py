import asyncio
from app.services.visual_analysis import visual_analysis_service
from dotenv import load_dotenv
import os

async def test_visual_analysis():
    # Load environment variables
    load_dotenv()
    
    # Check if Hugging Face API key is set
    huggingface_key = os.getenv("HUGGINGFACE_API_KEY")
    if not huggingface_key:
        print("❌ Error: HUGGINGFACE_API_KEY not found in environment variables")
        return
    else:
        print(f"✅ Found Hugging Face API key: {huggingface_key[:10]}...")
    
    # Test URL (using a public YouTube video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"\nTesting visual analysis for: {test_url}")
    print("This may take a few minutes depending on the video length...")
    
    try:
        # Analyze video with 2-second intervals between frames
        analysis = await visual_analysis_service.analyze_video(test_url, frame_interval=2)
        
        print("\n✅ Successfully analyzed video:")
        print(f"Analyzed {analysis['frame_count']} frames")
        print("\nDetected Objects:")
        for obj in analysis['detected_objects']:
            score = analysis['confidence_scores'].get(obj, 0)
            print(f"- {obj} (confidence: {score:.2f})")
            
        print("\nDetected Scenes:")
        for scene in analysis['detected_scenes']:
            score = analysis['confidence_scores'].get(scene, 0)
            print(f"- {scene} (confidence: {score:.2f})")
            
        print("\nDetected Text:")
        for text in analysis['detected_text']:
            score = analysis['confidence_scores'].get(text, 0)
            print(f"- {text} (confidence: {score:.2f})")
            
    except Exception as e:
        print("\n❌ Error analyzing video:")
        print(str(e))

if __name__ == "__main__":
    asyncio.run(test_visual_analysis()) 