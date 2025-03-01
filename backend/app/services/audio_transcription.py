import tempfile
import os
from typing import Dict, Any, List
import yt_dlp
from ..core.config import settings
import time
import ffmpeg
from openai import OpenAI
from supabase import create_client
import subprocess

class AudioTranscriptionService:
    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize Supabase client
        self.supabase = create_client(settings.SUPABASE_URL.strip(), settings.SUPABASE_KEY.strip())
        
        # yt-dlp configuration for getting direct audio URL
        self.ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',  # Prefer m4a/mp3 formats
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            # Add headers to avoid blocks
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        # Platform-specific options
        self.platform_opts = {
            'tiktok': {
                'format': 'bestaudio/best',  # TikTok needs video format
                'extract_audio': True,
                'force_generic_extractor': False,
            },
            'instagram': {
                'format': 'bestaudio/best',
                'extract_audio': True,
                'force_generic_extractor': False,
            },
            'facebook': {
                'format': 'bestaudio/best',
                'extract_audio': True,
                'force_generic_extractor': False,
            },
            'snapchat': {
                'format': 'bestaudio/best',
                'extract_audio': True,
                'force_generic_extractor': True,
            }
        }
        
        # Maximum duration in seconds (10 minutes per chunk)
        self.chunk_duration = 10 * 60

    def _clean_url(self, url: str) -> str:
        """Clean and normalize social media URLs."""
        # Remove tracking parameters and clean up the URL
        url = url.split('?')[0]  # Remove query parameters
        
        # Handle TikTok URLs
        if 'tiktok.com' in url:
            # Convert mobile URLs to desktop format
            url = url.replace('vm.tiktok.com', 'www.tiktok.com')
            # Remove unnecessary parts
            if '/v/' in url:
                url = f"https://www.tiktok.com/t/{url.split('/')[-1]}"
        
        # Handle Instagram URLs
        elif 'instagram.com' in url:
            # Ensure it's using www subdomain
            url = url.replace('//instagram.com', '//www.instagram.com')
        
        # Handle Facebook URLs
        elif 'facebook.com' in url or 'fb.watch' in url:
            # Convert fb.watch to full URL if needed
            if 'fb.watch' in url:
                url = f"https://www.facebook.com/watch?v={url.split('/')[-1]}"
        
        # Handle Snapchat URLs
        elif 'snapchat.com' in url:
            # Ensure using www subdomain
            url = url.replace('//snapchat.com', '//www.snapchat.com')
        
        return url

    def _get_platform(self, url: str) -> str:
        """Determine the platform from the URL."""
        url = url.lower()
        if 'tiktok.com' in url:
            return 'tiktok'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'facebook'
        elif 'snapchat.com' in url:
            return 'snapchat'
        else:
            return 'other'

    def _get_audio_url_and_duration(self, video_url: str) -> tuple[str, float]:
        """Get direct audio stream URL and duration from video URL."""
        try:
            # Clean the URL first
            video_url = self._clean_url(video_url)
            print(f"Cleaned URL: {video_url}")
            
            # Get platform-specific options
            platform = self._get_platform(video_url)
            print(f"Detected platform: {platform}")
            
            # Merge base options with platform-specific options
            ydl_opts = {**self.ydl_opts, **self.platform_opts.get(platform, {})}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(video_url, download=False)
                duration = float(info.get('duration', 0))
                
                # Get the best audio format URL
                formats = info.get('formats', [])
                
                def format_score(f):
                    """Calculate a score for format ranking."""
                    try:
                        has_audio = f.get('acodec', '') != 'none'
                        audio_only = f.get('vcodec', '') == 'none'
                        abr = float(f.get('abr', 0) or 0)  # Handle None
                        filesize = float(f.get('filesize', float('inf')) or float('inf'))  # Handle None
                        return (has_audio, audio_only, abr, -filesize)  # Negative filesize so smaller is better
                    except (TypeError, ValueError):
                        return (False, False, 0, -float('inf'))  # Lowest priority for invalid formats
                
                # Sort formats by score
                formats.sort(key=format_score, reverse=True)
                
                # Find the best audio format
                for format in formats:
                    if format.get('acodec') != 'none':  # Has audio
                        protocol = format.get('protocol', '')
                        # Prefer formats that work well with FFmpeg
                        if protocol in ['https', 'http', 'm3u8', 'dash'] and format.get('url'):
                            return format['url'], duration
                
                # If no suitable format found, try using the direct URL
                if info.get('url'):
                    return info['url'], duration
                
                raise Exception("No suitable audio format found")
                
        except Exception as e:
            raise Exception(f"Error getting audio URL: {str(e)}")

    def _stream_and_process_chunk(self, audio_url: str, start_time: int, duration: int) -> str:
        """Stream a chunk of audio and save it temporarily."""
        try:
            # Create temporary file for the chunk
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                chunk_path = temp_file.name
                
                # Use ffmpeg to stream and process the chunk
                ffmpeg_cmd = [
                    'ffmpeg', '-y',  # Overwrite output files
                    '-ss', str(start_time),  # Start time
                    '-t', str(duration),  # Duration
                    '-i', audio_url,  # Input URL
                    '-acodec', 'libmp3lame',  # MP3 codec
                    '-ar', '16000',  # Sample rate (required by Whisper)
                    '-ac', '1',  # Mono audio
                    '-ab', '128k',  # Audio bitrate
                    '-loglevel', 'error',  # Minimal logging
                    chunk_path  # Output file
                ]
                
                # Add user agent to avoid some streaming issues
                os.environ['FFMPEG_HTTP_USER_AGENT'] = 'Mozilla/5.0'
                
                subprocess.run(ffmpeg_cmd, check=True)
                return chunk_path
                
        except Exception as e:
            raise Exception(f"Error streaming audio chunk: {str(e)}")

    async def transcribe_chunk(self, chunk_path: str) -> Dict[str, Any]:
        """Transcribe a single audio chunk using OpenAI Whisper API."""
        try:
            with open(chunk_path, 'rb') as audio_file:
                # Send to OpenAI Whisper API
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
                
                return {
                    'text': response.text,
                    'segments': response.segments if hasattr(response, 'segments') else [],
                    'language': response.language if hasattr(response, 'language') else 'en'
                }
        finally:
            # Clean up temporary file
            try:
                os.unlink(chunk_path)
            except:
                pass

    async def transcribe_video(self, url: str, video_id: str = None) -> Dict[str, Any]:
        """
        Stream and transcribe audio from a video URL.
        
        Args:
            url: Video URL to transcribe
            video_id: Optional video ID for storing in Supabase
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            print(f"Getting audio stream URL from {url}...")
            audio_url, duration = self._get_audio_url_and_duration(url)
            print(f"Found audio stream (duration: {duration:.2f} seconds)")
            
            if duration == 0:
                print("Duration not available from metadata, probing stream...")
                # Try to get duration using ffprobe
                try:
                    probe = ffmpeg.probe(audio_url)
                    duration = float(probe['streams'][0]['duration'])
                except:
                    # If we can't get duration, assume it's short enough for one chunk
                    print("Could not determine duration, processing as single chunk...")
                    duration = self.chunk_duration
            
            # Calculate number of chunks
            num_chunks = max(1, int(duration / self.chunk_duration))
            
            # Process each chunk
            all_segments = []
            full_text = []
            detected_language = None
            
            print(f"Processing {num_chunks} chunks...")
            for i in range(num_chunks):
                start_time = i * self.chunk_duration
                chunk_duration = min(self.chunk_duration, duration - start_time)
                print(f"Processing chunk {i+1}/{num_chunks} (starting at {start_time:.2f} seconds)...")
                
                # Stream and process chunk
                chunk_path = self._stream_and_process_chunk(audio_url, start_time, chunk_duration)
                
                # Transcribe chunk
                result = await self.transcribe_chunk(chunk_path)
                
                full_text.append(result['text'])
                all_segments.extend(result['segments'])
                
                # Use the first detected language
                if not detected_language:
                    detected_language = result['language']
            
            # Combine results
            transcription = {
                'url': url,
                'transcription': ' '.join(full_text),
                'detected_language': detected_language,
                'segments': all_segments,
                'word_timestamps': []  # OpenAI Whisper doesn't provide word-level timestamps
            }
            
            # Store in Supabase if video_id is provided
            if video_id:
                try:
                    self.supabase.table('video_analysis').upsert({
                        'video_id': video_id,
                        'audio_transcription': transcription['transcription']
                    }).execute()
                except Exception as e:
                    print(f"Warning: Failed to store transcription in Supabase: {str(e)}")
            
            return transcription
            
        except Exception as e:
            raise Exception(f"Error transcribing video: {str(e)}")

# Initialize the audio transcription service
audio_transcription_service = AudioTranscriptionService() 