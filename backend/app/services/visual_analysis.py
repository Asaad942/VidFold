import numpy as np
from typing import List, Dict, Any
import requests
from datetime import datetime
import yt_dlp
import base64
import io
from PIL import Image
from ..core.config import settings

class VisualAnalysisService:
    def __init__(self):
        self.huggingface_token = settings.HUGGINGFACE_API_KEY
        # Using a model better suited for general image recognition and scene understanding
        self.api_url = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
        self.headers = {"Authorization": f"Bearer {self.huggingface_token}"}
        
        if not self.huggingface_token:
            raise ValueError("HUGGINGFACE_API_KEY must be provided")
        
        # yt-dlp configuration for frame extraction
        self.ydl_opts = {
            'format': 'best[height<=480]',  # Use medium quality for better frame extraction
            'extract_frames': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }

    async def analyze_video(self, url: str, frame_interval: int = 5) -> Dict[str, Any]:
        """
        Analyze video content by extracting frames directly from the video stream.
        No full video download required.
        
        Args:
            url: Video URL
            frame_interval: Interval between frames to analyze (in seconds)
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            print(f"Analyzing video stream from {url}...")
            
            # Get video info and duration
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get('duration', 0)
                
                if not duration:
                    raise Exception("Could not determine video duration")
                
                # Calculate frame timestamps to extract
                frame_timestamps = []
                current_time = 0
                while current_time < duration:
                    frame_timestamps.append(current_time)
                    current_time += frame_interval
                
                # Extract frames at specific timestamps using yt-dlp's frame extraction
                frames = []
                for timestamp in frame_timestamps:
                    try:
                        frame_data = ydl.extract_frame(
                            url,
                            timestamp=timestamp,
                            output_format='jpg'
                        )
                        if frame_data:
                            # Convert frame data to PIL Image
                            image = Image.open(io.BytesIO(frame_data))
                            # Convert to RGB format
                            image = image.convert('RGB')
                            frames.append(image)
                    except Exception as e:
                        print(f"Warning: Failed to extract frame at {timestamp}s: {str(e)}")
                        continue
                
                print(f"Analyzing {len(frames)} frames...")
                analysis_results = await self._analyze_frames(frames)
                
                # Process and combine results
                combined_results = self._combine_analysis_results(analysis_results)
                
                return {
                    'url': url,
                    'frame_count': len(frames),
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'detected_objects': combined_results['objects'],
                    'detected_scenes': combined_results['scenes'],
                    'detected_text': combined_results['text'],
                    'confidence_scores': combined_results['confidence_scores']
                }
                
        except Exception as e:
            raise Exception(f"Error analyzing video: {str(e)}")

    async def _analyze_frames(self, frames: List[Image.Image]) -> List[Dict[str, Any]]:
        """Send frames to Hugging Face API for analysis."""
        results = []
        try:
            for i, frame in enumerate(frames):
                print(f"Analyzing frame {i+1}/{len(frames)}...")
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                frame.save(img_byte_arr, format='JPEG')
                frame_bytes = img_byte_arr.getvalue()
                
                # Send to Hugging Face API
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=frame_bytes
                )
                response.raise_for_status()
                results.append(response.json())
                
            return results
            
        except Exception as e:
            raise Exception(f"Error analyzing frames with Hugging Face API: {str(e)}")

    def _combine_analysis_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine and process results from multiple frames."""
        all_objects = set()
        all_scenes = set()
        all_text = set()
        confidence_scores = {}
        
        for result in results:
            # DETR model returns a list of detections
            for detection in result:
                label = detection.get('label', '').lower()
                score = detection.get('score', 0)
                confidence = float(score)
                
                # Categorize the detection
                if any(word in label for word in ['person', 'human', 'man', 'woman']):
                    all_objects.add(label)
                elif any(word in label for word in ['text', 'sign', 'banner']):
                    all_text.add(label)
                else:
                    all_scenes.add(label)
                    
                # Update confidence scores
                if label in confidence_scores:
                    confidence_scores[label] = max(confidence_scores[label], confidence)
                else:
                    confidence_scores[label] = confidence
        
        return {
            'objects': list(all_objects),
            'scenes': list(all_scenes),
            'text': list(all_text),
            'confidence_scores': confidence_scores
        }

# Initialize the visual analysis service
visual_analysis_service = VisualAnalysisService() 