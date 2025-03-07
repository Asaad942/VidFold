"""
Browser service for handling browser operations
"""
import logging
import base64
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

logger = logging.getLogger(__name__)

class BrowserService:
    _instance = None
    _lock = asyncio.Lock()
    _last_activity = datetime.now()
    _cleanup_task = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize browser service"""
        if not hasattr(self, 'initialized'):
            self.playwright = None
            self.browser = None
            self.context = None
            self.active_pages = set()
            self.initialized = True

    async def initialize(self):
        """Initialize browser and context"""
        async with self._lock:
            if self.browser is None:
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
                    self._start_cleanup_task()
                except Exception as e:
                    logger.error(f"Failed to initialize browser service: {str(e)}")
                    raise

    def _start_cleanup_task(self):
        """Start the cleanup task if not already running"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Background task to clean up inactive browser"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                if datetime.now() - self._last_activity > timedelta(minutes=10):
                    logger.info("Browser inactive for 10 minutes, cleaning up...")
                    await self.cleanup()
                    break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def cleanup(self):
        """Clean up browser resources"""
        async with self._lock:
            try:
                # Close all active pages
                for page in self.active_pages:
                    try:
                        await page.close()
                    except Exception as e:
                        logger.error(f"Error closing page: {str(e)}")
                self.active_pages.clear()

                if self.context:
                    await self.context.close()
                    self.context = None
                if self.browser:
                    await self.browser.close()
                    self.browser = None
                if self.playwright:
                    await self.playwright.stop()
                    self.playwright = None
                logger.info("Browser service cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up browser service: {str(e)}")

    async def _get_page(self) -> Page:
        """Get a new page and track it"""
        if not self.context:
            await self.initialize()
        page = await self.context.new_page()
        self.active_pages.add(page)
        self._last_activity = datetime.now()
        return page

    async def _release_page(self, page: Page):
        """Release a page and remove it from tracking"""
        try:
            await page.close()
            self.active_pages.remove(page)
        except Exception as e:
            logger.error(f"Error releasing page: {str(e)}")

    async def capture_video_frames(self, url: str, interval: int = 5, max_frames: int = 10) -> List[Dict[str, Any]]:
        """Capture frames from a video URL"""
        page = None
        try:
            page = await self._get_page()
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
            
            return frames
            
        except Exception as e:
            logger.error(f"Error capturing video frames: {str(e)}")
            raise
        finally:
            if page:
                await self._release_page(page)

    async def capture_video_audio(self, url: str, duration: int = 300) -> bytes:
        """Capture audio from a video URL"""
        page = None
        try:
            page = await self._get_page()
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
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error capturing video audio: {str(e)}")
            raise
        finally:
            if page:
                await self._release_page(page)

    async def get_youtube_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata from YouTube video"""
        page = None
        try:
            page = await self._get_page()
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
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting YouTube metadata: {str(e)}")
            raise
        finally:
            if page:
                await self._release_page(page)

    async def get_instagram_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata from Instagram video"""
        page = None
        try:
            page = await self._get_page()
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
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting Instagram metadata: {str(e)}")
            raise
        finally:
            if page:
                await self._release_page(page)

    async def get_tiktok_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata from TikTok video"""
        page = None
        try:
            page = await self._get_page()
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
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting TikTok metadata: {str(e)}")
            raise
        finally:
            if page:
                await self._release_page(page)

    async def get_facebook_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata from Facebook video"""
        page = None
        try:
            page = await self._get_page()
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
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting Facebook metadata: {str(e)}")
            raise
        finally:
            if page:
                await self._release_page(page)

# Create a singleton instance
browser_service = BrowserService() 