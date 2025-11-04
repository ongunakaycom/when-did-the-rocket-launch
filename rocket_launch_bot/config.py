import os
from typing import Optional

class Config:
    """Configuration management for the bot"""

    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # FrameX API
    API_BASE: str = os.getenv("API_BASE", "https://framex-develop-amzw3.ondigitalocean.app/api/")
    VIDEO_NAME: str = os.getenv("VIDEO_NAME", "Falcon Heavy Test Flight (Hosted Webcast)-wbSwFU6tY1c")

    # Bot settings
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30

    @classmethod
    def validate(cls) -> Optional[str]:
        """Validate configuration and return error message if invalid"""
        if not cls.BOT_TOKEN:
            return "TELEGRAM_BOT_TOKEN environment variable is required"
        return None