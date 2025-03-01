import re
from ..schemas.video import Platform

class URLParser:
    @staticmethod
    def detect_platform(url: str) -> Platform:
        """
        Detect the platform from a video URL.
        """
        patterns = {
            Platform.YOUTUBE: [
                r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]+)',
            ],
            Platform.INSTAGRAM: [
                r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)',
            ],
            Platform.TIKTOK: [
                r'(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com\/@[\w.-]+\/video\/|vm\.tiktok\.com\/)(\d+)',
            ],
            Platform.FACEBOOK: [
                r'(?:https?:\/\/)?(?:www\.)?facebook\.com\/(?:watch\/\?v=|video\.php\?v=)(\d+)',
                r'(?:https?:\/\/)?(?:www\.)?fb\.watch\/([a-zA-Z0-9_-]+)',
            ]
        }

        for platform, platform_patterns in patterns.items():
            for pattern in platform_patterns:
                if re.search(pattern, url):
                    return platform
        
        return Platform.UNKNOWN

    @staticmethod
    def validate_url(url: str, platform: Platform) -> bool:
        """
        Validate if the URL matches the specified platform.
        If platform is UNKNOWN, detect platform from URL.
        """
        if platform == Platform.UNKNOWN:
            detected_platform = URLParser.detect_platform(url)
            return detected_platform != Platform.UNKNOWN
        
        # If platform is specified, validate URL matches that platform
        patterns = {
            Platform.YOUTUBE: [
                r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]+)',
            ],
            Platform.INSTAGRAM: [
                r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)',
            ],
            Platform.TIKTOK: [
                r'(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com\/@[\w.-]+\/video\/|vm\.tiktok\.com\/)(\d+)',
            ],
            Platform.FACEBOOK: [
                r'(?:https?:\/\/)?(?:www\.)?facebook\.com\/(?:watch\/\?v=|video\.php\?v=)(\d+)',
                r'(?:https?:\/\/)?(?:www\.)?fb\.watch\/([a-zA-Z0-9_-]+)',
            ]
        }

        if platform not in patterns:
            return False

        for pattern in patterns[platform]:
            if re.search(pattern, url):
                return True
        
        return False

    @staticmethod
    def extract_video_id(url: str, platform: Platform) -> str:
        """
        Extract the video ID from a URL for a specific platform.
        """
        patterns = {
            Platform.YOUTUBE: [
                r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]+)',
            ],
            Platform.INSTAGRAM: [
                r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)',
            ],
            Platform.TIKTOK: [
                r'(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com\/@[\w.-]+\/video\/|vm\.tiktok\.com\/)(\d+)',
            ],
            Platform.FACEBOOK: [
                r'(?:https?:\/\/)?(?:www\.)?facebook\.com\/(?:watch\/\?v=|video\.php\?v=)(\d+)',
                r'(?:https?:\/\/)?(?:www\.)?fb\.watch\/([a-zA-Z0-9_-]+)',
            ]
        }

        if platform not in patterns:
            return None

        for pattern in patterns[platform]:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None 