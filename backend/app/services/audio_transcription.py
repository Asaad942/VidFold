import logging
from typing import Dict, Any
import base64
import io
from ..core.config import settings
from .browser_service import browser_service

logger = logging.getLogger(__name__)

class AudioTranscriptionService:
    def __init__(self):
        self.huggingface_token = settings.HUGGINGFACE_API_KEY
        self.api_url = "https://api-inference.huggingface.co/models/facebook/wav2vec2-base-960h"
        self.headers = {"Authorization": f"Bearer {self.huggingface_token}"}
        
        if not self.huggingface_token:
            raise ValueError("HUGGINGFACE_API_KEY must be provided")

    async def transcribe_video(self, url: str, video_id: str = None) -> Dict[str, Any]:
        """
        Transcribe audio from a video URL using browser-based audio capture.
        
        Args:
            url: The video URL to transcribe
            video_id: Optional video ID for tracking
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            logger.info(f"Starting audio transcription for URL: {url}")
            
            # Capture audio from the video using browser service
            audio_data = await browser_service.capture_video_audio(
                url,
                duration=300  # Capture up to 5 minutes of audio
            )
            
            if not audio_data:
                raise Exception("No audio captured from video")
            
            # Send audio data to Hugging Face API for transcription
            response = await self._send_to_huggingface(audio_data)
            
            # Process and format the transcription results
            results = self._process_transcription_results(response)
            
            logger.info(f"Successfully transcribed audio from {url}")
            return results
            
        except Exception as e:
            logger.error(f"Error transcribing video audio: {str(e)}")
            raise

    async def _send_to_huggingface(self, audio_data: bytes) -> Dict[str, Any]:
        """Send audio data to Hugging Face API for transcription"""
        try:
            # Send audio data to Hugging Face API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=audio_data
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending audio to Hugging Face API: {str(e)}")
            raise

    def _process_transcription_results(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process and format transcription results"""
        try:
            # Extract text from response
            text = response.get('text', '')
            
            # Split into sentences
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            
            # Calculate statistics
            word_count = len(text.split())
            sentence_count = len(sentences)
            
            return {
                'text': text,
                'sentences': sentences,
                'statistics': {
                    'word_count': word_count,
                    'sentence_count': sentence_count,
                    'average_words_per_sentence': word_count / sentence_count if sentence_count > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing transcription results: {str(e)}")
            raise

# Initialize the audio transcription service
audio_transcription_service = AudioTranscriptionService() 