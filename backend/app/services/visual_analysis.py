import cv2
import numpy as np
from typing import List, Dict, Any
import requests
import os
from datetime import datetime
import tempfile
import yt_dlp
from ..core.config import settings

class VisualAnalysisService:
    def __init__(self):
        self.huggingface_token = settings.HUGGINGFACE_API_KEY
        # Using a model better suited for general image recognition and scene understanding
        self.api_url = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
        self.headers = {"Authorization": f"Bearer {self.huggingface_token}"}
        
        if not self.huggingface_token:
            raise ValueError("HUGGINGFACE_API_KEY must be provided")
        
        # yt-dlp configuration for video download
        self.ydl_opts = {
            'format': 'worst[ext=mp4]',  # Use lowest quality to save bandwidth
            'quiet': True,
            'no_warnings': True
        }

    async def analyze_video(self, url: str, frame_interval: int = 1) -> Dict[str, Any]:
        """
        Analyze video content by extracting frames and using Hugging Face for object detection.
        
        Args:
            url: Video URL
            frame_interval: Interval between frames to analyze (in seconds)
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            print(f"Downloading video from {url}...")
            # Download video to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                video_path = temp_file.name
                
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Get the downloaded file path from yt-dlp
                video_path = ydl.prepare_filename(info)
            
            print("Extracting frames...")
            # Extract and analyze frames
            frames = self._extract_frames(video_path, frame_interval)
            print(f"Analyzing {len(frames)} frames...")
            analysis_results = await self._analyze_frames(frames)
            
            # Clean up temporary file
            try:
                os.unlink(video_path)
            except:
                pass  # Ignore cleanup errors
            
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

    def _extract_frames(self, video_path: str, interval: int) -> List[np.ndarray]:
        """Extract frames from video at specified intervals."""
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_jump = int(fps * interval)
            
            while cap.isOpened():
                # Jump to next frame interval
                for _ in range(frame_jump):
                    cap.read()
                    
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                
            cap.release()
            return frames
            
        except Exception as e:
            raise Exception(f"Error extracting frames: {str(e)}")

    async def _analyze_frames(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Send frames to Hugging Face API for analysis."""
        results = []
        try:
            for i, frame in enumerate(frames):
                print(f"Analyzing frame {i+1}/{len(frames)}...")
                # Convert numpy array to bytes
                _, encoded_frame = cv2.imencode('.jpg', frame)
                frame_bytes = encoded_frame.tobytes()
                
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