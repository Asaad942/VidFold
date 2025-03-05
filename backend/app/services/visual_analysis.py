import numpy as np
from typing import List, Dict, Any
import requests
from datetime import datetime
import yt_dlp
import base64
import io
from PIL import Image
from ..core.config import settings
import logging
import cv2
from io import BytesIO
import tensorflow as tf
import tensorflow_hub as hub

logger = logging.getLogger(__name__)

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
            }],
            # Add headers to avoid blocks
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            # Server-friendly options
            'no_check_certificates': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'geo_verification_proxy': None,
            'source_address': '0.0.0.0',
            'sleep_interval': 5,
            'max_sleep_interval': 10,
            'sleep_interval_requests': 3,
        }

        # Load the MobileNet model for image classification
        self.model = hub.load('https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/4')
        self.input_size = (224, 224)
        
        # Load COCO dataset labels
        self.labels = self._load_coco_labels()

    def _load_coco_labels(self) -> List[str]:
        """Load COCO dataset labels for object detection"""
        try:
            # Load labels from a file or URL
            # For now, returning a simplified list
            return [
                'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
                'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
                'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
                'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella',
                'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
                'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
                'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork',
                'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
                'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
                'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv',
                'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
                'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
                'scissors', 'teddy bear', 'hair drier', 'toothbrush'
            ]
        except Exception as e:
            logger.error(f"Error loading COCO labels: {str(e)}")
            return []

    def _base64_to_image(self, base64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 string
            image_data = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            return Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error(f"Error converting base64 to image: {str(e)}")
            raise

    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for model input"""
        try:
            # Resize image
            image = image.resize(self.input_size)
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Normalize pixel values
            img_array = img_array / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise

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

    async def analyze_frames(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a list of video frames.
        
        Args:
            frames: List of dictionaries containing frame data and timestamps
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info(f"Starting analysis of {len(frames)} frames")
            
            all_objects = []
            all_scenes = []
            
            for frame in frames:
                try:
                    # Convert base64 to image
                    image = self._base64_to_image(frame['frame_data'])
                    
                    # Preprocess image
                    processed_image = self._preprocess_image(image)
                    
                    # Get model predictions
                    predictions = self.model(processed_image)
                    
                    # Get top 5 predictions
                    top_5_indices = np.argsort(predictions[0])[-5:][::-1]
                    top_5_labels = [self.labels[i] for i in top_5_indices]
                    top_5_scores = predictions[0][top_5_indices].numpy()
                    
                    # Add frame analysis results
                    frame_analysis = {
                        'timestamp': frame['timestamp'],
                        'frame_number': frame['frame_number'],
                        'objects': [
                            {'label': label, 'confidence': float(score)}
                            for label, score in zip(top_5_labels, top_5_scores)
                        ]
                    }
                    
                    all_objects.extend(top_5_labels)
                    all_scenes.append(frame_analysis)
                    
                except Exception as e:
                    logger.error(f"Error analyzing frame {frame.get('frame_number')}: {str(e)}")
                    continue
            
            # Calculate overall statistics
            unique_objects = list(set(all_objects))
            object_counts = {obj: all_objects.count(obj) for obj in unique_objects}
            
            # Create analysis results
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_frames_analyzed': len(frames),
                'unique_objects': unique_objects,
                'object_counts': object_counts,
                'frame_analysis': all_scenes,
                'summary': {
                    'most_common_objects': sorted(
                        object_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                }
            }
            
            logger.info(f"Analysis completed successfully: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_frames: {str(e)}")
            raise

# Initialize the visual analysis service
visual_analysis_service = VisualAnalysisService() 