import os
from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@db:5432/tiktok_shorts"
    
    # Redis settings for Celery
    REDIS_URL: str = "redis://redis:6379/0"
    
    # File storage settings
    UPLOAD_DIR: Path = Path("uploads")
    PROCESSED_DIR: Path = Path("processed")
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # YouTube API settings
    YOUTUBE_CLIENT_SECRETS_FILE: str = "client_secrets.json"
    YOUTUBE_CREDENTIALS_PATH: str = "token.pickle"
    
    # Video processing settings
    CHECK_SUBTITLE_FRAMES: int = 10  # Number of frames to check for existing subtitles
    SUBTITLE_FONT_SIZE: int = 24
    SUBTITLE_FONT_COLOR: str = "white"
    SUBTITLE_BACKGROUND: bool = True
    SUBTITLE_POSITION: str = "bottom"  # 'top' or 'bottom'
    
    # Shorts settings
    MAX_VIDEO_LENGTH: int = 60  # seconds
    TARGET_RESOLUTION: tuple = (1080, 1920)  # Shorts vertical format
    
    class Config:
        env_file = ".env"

    def create_directories(self):
        """Create necessary directories if they don't exist."""
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.PROCESSED_DIR.mkdir(exist_ok=True)

# Create global settings instance
settings = Settings()
settings.create_directories()

def get_settings():
    """Dependency for FastAPI to get settings."""
    return settings