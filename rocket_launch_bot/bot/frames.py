import io
from typing import List, NamedTuple
from urllib.parse import quote, urljoin

import httpx
from PIL import Image

from config import Config


class VideoInfo(NamedTuple):
    """Represents video metadata from FrameX API"""
    name: str
    width: int
    height: int
    frames: int
    frame_rate: List[int]
    url: str
    first_frame: str
    last_frame: str


class FrameXClient:
    """Client for FrameX API with proper error handling"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT)
        self.base_url = Config.API_BASE
    
    async def get_video_info(self, video_name: str) -> VideoInfo:
        """Fetch video metadata"""
        url = urljoin(self.base_url, f"video/{quote(video_name)}/")
        response = await self.client.get(url)
        response.raise_for_status()
        return VideoInfo(**response.json())
    
    async def get_frame_image(self, video_name: str, frame_number: int) -> bytes:
        """Fetch frame image data"""
        url = urljoin(self.base_url, f'video/{quote(video_name)}/frame/{quote(str(frame_number))}/')
        response = await self.client.get(url)
        response.raise_for_status()
        return response.content
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class FrameProcessor:
    """Handles frame image processing"""
    
    @staticmethod
    async def resize_frame(image_data: bytes, max_size: tuple = (480, 270)) -> bytes:
        """Resize frame image for Telegram"""
        image = Image.open(io.BytesIO(image_data))
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()


class BisectionAlgorithm:
    """Implements the bisection algorithm for frame detection"""
    
    @staticmethod
    async def find_launch_frame(
        total_frames: int,
        frame_getter: callable,
        frame_tester: callable
    ) -> int:
        """
        Find the first frame where rocket launches using bisection
        
        Args:
            total_frames: Total number of frames in video
            frame_getter: Async function to get frame data by number
            frame_tester: Async function to test if rocket has launched in frame
            
        Returns:
            Frame number where launch occurs
        """
        if total_frames < 1:
            raise ValueError("Cannot bisect empty frame array")
        
        left = 0
        right = total_frames - 1
        
        while left + 1 < right:
            mid = (left + right) // 2
            
            frame_data = await frame_getter(mid)
            has_launched = await frame_tester(frame_data, mid)
            
            if has_launched:
                right = mid
            else:
                left = mid
        
        return right