from typing import List, Optional, Dict, Any
import asyncio
import logging
from playwright.async_api import async_playwright
import base64
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class BrowserService:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize the browser and context"""
        if not self.is_initialized:
            try:
                playwright = await async_playwright().start()
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                self.page = await self.context.new_page()
                self.is_initialized = True
                logger.info("Browser service initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing browser service: {str(e)}")
                raise

    async def capture_video_frames(self, url: str, interval: int = 5, max_frames: int = 10) -> List[Dict[str, Any]]:
        """
        Capture frames from a video URL using a headless browser.
        
        Args:
            url: The video URL to capture frames from
            interval: Time interval between frame captures in seconds
            max_frames: Maximum number of frames to capture
            
        Returns:
            List of dictionaries containing frame data and timestamps
        """
        try:
            await self.initialize()
            
            logger.info(f"Navigating to URL: {url}")
            await self.page.goto(url, wait_until='networkidle')
            
            # Wait for video element to be present
            await self.page.wait_for_selector('video', timeout=10000)
            
            # Start video playback
            await self.page.evaluate('''() => {
                const video = document.querySelector('video');
                if (video) {
                    video.play();
                }
            }''')
            
            frames = []
            frame_count = 0
            
            while frame_count < max_frames:
                try:
                    # Wait for the specified interval
                    await asyncio.sleep(interval)
                    
                    # Take a screenshot
                    screenshot = await self.page.screenshot(
                        type='jpeg',
                        quality=80,
                        full_page=False
                    )
                    
                    # Convert to base64
                    frame_base64 = base64.b64encode(screenshot).decode('utf-8')
                    
                    # Add frame data
                    frames.append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'frame_number': frame_count,
                        'frame_data': frame_base64
                    })
                    
                    frame_count += 1
                    logger.info(f"Captured frame {frame_count}/{max_frames}")
                    
                except Exception as e:
                    logger.error(f"Error capturing frame {frame_count}: {str(e)}")
                    break
            
            return frames
            
        except Exception as e:
            logger.error(f"Error in capture_video_frames: {str(e)}")
            raise

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            self.is_initialized = False
            logger.info("Browser service cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up browser service: {str(e)}")
            raise

# Create a singleton instance
browser_service = BrowserService() 