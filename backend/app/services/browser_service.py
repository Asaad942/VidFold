"""
Browser service for handling browser operations
"""
import logging
import base64
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class BrowserService:
    def __init__(self):
        """Initialize browser service"""
        self.playwright = None
        self.browser = None
        self.context = None

    async def initialize(self):
        """Initialize browser and context"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            logger.info("Browser service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser service: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser service cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up browser service: {str(e)}")

    async def capture_video_frames(self, url: str, interval: int = 5, max_frames: int = 10) -> List[Dict[str, Any]]:
        """
        Capture frames from a video URL
        
        Args:
            url: Video URL
            interval: Time interval between frames in seconds
            max_frames: Maximum number of frames to capture
            
        Returns:
            List of dictionaries containing frame data and timestamps
        """
        try:
            if not self.context:
                await self.initialize()
                
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await page.wait_for_selector('video', timeout=10000)
            
            # Start video playback
            await page.evaluate('''() => {
                const video = document.querySelector('video');
                if (video) {
                    video.play();
                }
            }''')
            
            frames = []
            frame_count = 0
            
            while frame_count < max_frames:
                # Capture screenshot
                screenshot = await page.screenshot(type='jpeg', quality=80)
                frame_data = base64.b64encode(screenshot).decode('utf-8')
                
                frames.append({
                    'frame_data': frame_data,
                    'timestamp': frame_count * interval
                })
                
                frame_count += 1
                await asyncio.sleep(interval)
            
            await page.close()
            return frames
            
        except Exception as e:
            logger.error(f"Error capturing video frames: {str(e)}")
            raise

    async def capture_video_audio(self, url: str, duration: int = 300) -> bytes:
        """
        Capture audio from a video URL
        
        Args:
            url: Video URL
            duration: Maximum duration to capture in seconds
            
        Returns:
            Audio data as bytes
        """
        try:
            if not self.context:
                await self.initialize()
                
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await page.wait_for_selector('video', timeout=10000)
            
            # Start video playback
            await page.evaluate('''() => {
                const video = document.querySelector('video');
                if (video) {
                    video.play();
                }
            }''')
            
            # Create audio context and media stream
            audio_data = await page.evaluate('''async (duration) => {
                const audioContext = new AudioContext();
                const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const source = audioContext.createMediaStreamSource(mediaStream);
                const processor = audioContext.createScriptProcessor(4096, 1, 1);
                
                source.connect(processor);
                processor.connect(audioContext.destination);
                
                const chunks = [];
                processor.onaudioprocess = (e) => {
                    chunks.push(e.inputBuffer.getChannelData(0));
                };
                
                await new Promise(resolve => setTimeout(resolve, duration * 1000));
                
                const audioBuffer = audioContext.createBuffer(1, chunks.length * 4096, audioContext.sampleRate);
                const channelData = audioBuffer.getChannelData(0);
                
                for (let i = 0; i < chunks.length; i++) {
                    channelData.set(chunks[i], i * 4096);
                }
                
                return audioBuffer;
            }''', duration)
            
            await page.close()
            return audio_data
            
        except Exception as e:
            logger.error(f"Error capturing video audio: {str(e)}")
            raise

    async def get_youtube_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get metadata from YouTube video
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            if not self.context:
                await self.initialize()
                
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await page.wait_for_selector('video', timeout=10000)
            
            # Extract metadata
            metadata = await page.evaluate('''() => {
                const video = document.querySelector('video');
                const title = document.title;
                const description = document.querySelector('meta[name="description"]')?.content;
                const thumbnail = document.querySelector('link[rel="image_src"]')?.href;
                const duration = video?.duration;
                
                return {
                    title,
                    description,
                    thumbnail_url: thumbnail,
                    duration: duration ? Math.floor(duration) : null,
                    platform: 'youtube'
                };
            }''')
            
            await page.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting YouTube metadata: {str(e)}")
            raise

    async def get_instagram_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get metadata from Instagram video
        
        Args:
            url: Instagram video URL
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            if not self.context:
                await self.initialize()
                
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await page.wait_for_selector('video', timeout=10000)
            
            # Extract metadata
            metadata = await page.evaluate('''() => {
                const video = document.querySelector('video');
                const title = document.title;
                const description = document.querySelector('meta[name="description"]')?.content;
                const thumbnail = document.querySelector('link[rel="image_src"]')?.href;
                const duration = video?.duration;
                
                return {
                    title,
                    description,
                    thumbnail_url: thumbnail,
                    duration: duration ? Math.floor(duration) : null,
                    platform: 'instagram'
                };
            }''')
            
            await page.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting Instagram metadata: {str(e)}")
            raise

    async def get_tiktok_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get metadata from TikTok video
        
        Args:
            url: TikTok video URL
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            if not self.context:
                await self.initialize()
                
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await page.wait_for_selector('video', timeout=10000)
            
            # Extract metadata
            metadata = await page.evaluate('''() => {
                const video = document.querySelector('video');
                const title = document.title;
                const description = document.querySelector('meta[name="description"]')?.content;
                const thumbnail = document.querySelector('link[rel="image_src"]')?.href;
                const duration = video?.duration;
                
                return {
                    title,
                    description,
                    thumbnail_url: thumbnail,
                    duration: duration ? Math.floor(duration) : null,
                    platform: 'tiktok'
                };
            }''')
            
            await page.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting TikTok metadata: {str(e)}")
            raise

    async def get_facebook_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get metadata from Facebook video
        
        Args:
            url: Facebook video URL
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            if not self.context:
                await self.initialize()
                
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await page.wait_for_selector('video', timeout=10000)
            
            # Extract metadata
            metadata = await page.evaluate('''() => {
                const video = document.querySelector('video');
                const title = document.title;
                const description = document.querySelector('meta[name="description"]')?.content;
                const thumbnail = document.querySelector('link[rel="image_src"]')?.href;
                const duration = video?.duration;
                
                return {
                    title,
                    description,
                    thumbnail_url: thumbnail,
                    duration: duration ? Math.floor(duration) : null,
                    platform: 'facebook'
                };
            }''')
            
            await page.close()
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting Facebook metadata: {str(e)}")
            raise

# Initialize browser service
browser_service = BrowserService() 