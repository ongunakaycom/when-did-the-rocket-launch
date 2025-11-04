import io
from typing import List, NamedTuple
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
    """Mock Client for FrameX API - Works on PythonAnywhere free tier"""

    def __init__(self):
        self.video_info = VideoInfo(
            name="Falcon Heavy Test Flight (Hosted Webcast)-wbSwFU6tY1c",
            width=1280,
            height=720,
            frames=61696,  # Actual frame count from the video
            frame_rate=[30, 1],
            url="https://framex.wadledot.com/api/video/Falcon%20Heavy%20Test%20Flight%20%28Hosted%20Webcast%29-wbSwFU6tY1c/",
            first_frame="https://framex.wadledot.com/api/video/Falcon%20Heavy%20Test%20Flight%20%28Hosted%20Webcast%29-wbSwFU6tY1c/frame/0/",
            last_frame="https://framex.wadledot.com/api/video/Falcon%20Heavy%20Test%20Flight%20%28Hosted%20Webcast%29-wbSwFU6tY1c/frame/61695/"
        )

    async def get_video_info(self, video_name: str) -> VideoInfo:
        """Return mock video metadata"""
        print("DEBUG: Using mock video info")
        return self.video_info

    async def get_frame_image(self, video_name: str, frame_number: int) -> bytes:
        """Generate a mock frame image with frame number overlay"""
        print(f"DEBUG: Generating mock frame {frame_number}")
        try:
            # Create a simple image with frame number text
            from PIL import Image, ImageDraw, ImageFont
            import io

            # Create a blank image
            img = Image.new('RGB', (800, 600), color=(50, 50, 80))
            draw = ImageDraw.Draw(img)

            # Add frame number text
            try:
                # Try to use a font
                font = ImageFont.load_default()
                draw.text((400, 300), f"Frame: {frame_number}", fill=(255, 255, 255), font=font, anchor="mm")
            except:
                draw.text((400, 300), f"Frame: {frame_number}", fill=(255, 255, 255), anchor="mm")

            # Add instruction text
            draw.text((400, 350), "Mock frame for testing", fill=(200, 200, 200), anchor="mm")
            draw.text((400, 380), f"Total frames: {self.video_info.frames:,}", fill=(200, 200, 200), anchor="mm")

            # Convert to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()

        except Exception as e:
            # Fallback: create a simple colored image based on frame number
            import io
            from PIL import Image

            # Create a gradient based on frame number
            color_value = (frame_number * 10) % 255
            img = Image.new('RGB', (800, 600), color=(color_value, 50, 100))
            output = io.BytesIO()
            img.save(output, format='JPEG')
            return output.getvalue()

    async def close(self):
        """Mock close method"""
        pass


class FrameProcessor:
    """Handles frame image processing for Telegram"""

    @staticmethod
    async def prepare_frame_for_telegram(image_data: bytes, max_size: tuple = (800, 600)) -> bytes:
        """Resize and optimize frame image for Telegram"""
        try:
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except Exception as e:
            raise Exception(f"Failed to process frame image: {e}")