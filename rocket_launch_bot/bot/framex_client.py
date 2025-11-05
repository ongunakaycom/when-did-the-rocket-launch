import io
import requests
import logging
from typing import List, NamedTuple, Optional
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)

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
    """Real Client for FrameX API"""

    def __init__(self):
        self.base_url = Config.API_BASE
        self.session = requests.Session()
        self.session.timeout = Config.REQUEST_TIMEOUT

    def get_video_info(self, video_name: str) -> VideoInfo:
        """Get real video metadata from FrameX API"""
        try:
            response = self.session.get(f"{self.base_url}video/")
            response.raise_for_status()
            videos = response.json()
            
            # Find the requested video
            for video in videos:
                if video['name'] == video_name:
                    return VideoInfo(
                        name=video['name'],
                        width=video['width'],
                        height=video['height'],
                        frames=video['frames'],
                        frame_rate=video['frame_rate'],
                        url=video['url'],
                        first_frame=video['first_frame'],
                        last_frame=video['last_frame']
                    )
            
            raise Exception(f"Video '{video_name}' not found in API response")
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise Exception(f"Failed to get video info: {str(e)}")

    def get_frame_image(self, video_name: str, frame_number: int) -> bytes:
        """Get real frame image from FrameX API"""
        try:
            # Build the frame URL
            frame_url = f"{self.base_url}video/{video_name}/frame/{frame_number}/"
            
            response = self.session.get(frame_url)
            response.raise_for_status()
            image_data = response.content
            logger.info(f"Successfully fetched frame {frame_number} from API")
            return image_data
            
        except Exception as e:
            logger.error(f"Error getting frame {frame_number}: {e}")
            raise Exception(f"Failed to get frame {frame_number}: {str(e)}")

    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()

class FrameProcessor:
    """Handles frame image processing for Telegram"""

    @staticmethod
    def prepare_frame_for_telegram(image_data: bytes, max_size: tuple = (800, 600)) -> bytes:
        """Resize and optimize frame image for Telegram"""
        try:
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except Exception as e:
            raise Exception(f"Failed to process frame image: {e}")