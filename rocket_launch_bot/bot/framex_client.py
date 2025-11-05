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
        self.base_url = Config.API_BASE.rstrip('/') + '/'  # Ensure proper formatting
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
        """Get frame image from FrameX API"""
        try:
            logger.info(f"Fetching frame {frame_number} for video {video_name}")
            
            # CORRECTED URL FORMAT: base_url + video/VIDEO_NAME/frame/FRAME_NUMBER/
            url = f"{self.base_url}video/{video_name}/frame/{frame_number}/"
            logger.info(f"Requesting URL: {url}")
            
            response = self.session.get(url)
            
            if response.status_code != 200:
                logger.error(f"FrameX API error: {response.status_code} for frame {frame_number}")
                logger.error(f"Response content: {response.text[:200]}")
                raise Exception(f"Failed to fetch frame {frame_number} - Status: {response.status_code}")
            
            frame_data = response.content
            if not frame_data:
                logger.error(f"Empty frame data for frame {frame_number}")
                raise Exception(f"Empty frame data for frame {frame_number}")
                
            # Check if we got a valid image (JPEG should start with FF D8 FF)
            if len(frame_data) < 10 or not frame_data.startswith(b'\xff\xd8\xff'):
                logger.error(f"Invalid image data for frame {frame_number}")
                raise Exception(f"Invalid image data received for frame {frame_number}")
                
            logger.info(f"Successfully fetched frame {frame_number}, size: {len(frame_data)} bytes")
            return frame_data
            
        except Exception as e:
            logger.error(f"Error fetching frame {frame_number}: {e}")
            raise

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
            # Check if we have valid image data
            if not image_data:
                raise Exception("Empty image data received")
                
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            processed_data = output.getvalue()
            
            if not processed_data:
                raise Exception("Failed to process image - empty output")
                
            return processed_data
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            raise Exception(f"Failed to process frame image: {e}")