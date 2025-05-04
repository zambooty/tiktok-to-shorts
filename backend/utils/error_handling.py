from fastapi import HTTPException
from typing import Optional, Dict, Any
from .logging_config import CustomLogger, api_logger

class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    def __init__(self, message: str, video_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.video_id = video_id
        self.details = details or {}
        super().__init__(self.message)

class SubtitleDetectionError(VideoProcessingError):
    """Raised when subtitle detection fails."""
    pass

class VideoUploadError(VideoProcessingError):
    """Raised when video upload to YouTube fails."""
    pass

class ProcessingTimeoutError(VideoProcessingError):
    """Raised when video processing exceeds maximum time."""
    pass

class ValidationError(VideoProcessingError):
    """Raised when video validation fails (format, size, etc)."""
    pass

def handle_processing_error(error: Exception, logger: CustomLogger) -> HTTPException:
    """Convert processing errors to appropriate HTTP responses."""
    
    if isinstance(error, SubtitleDetectionError):
        logger.error("Subtitle detection failed", 
                    exc_info=error,
                    video_id=error.video_id,
                    **error.details)
        return HTTPException(
            status_code=422,
            detail={
                "message": "Failed to detect or generate subtitles",
                "video_id": error.video_id,
                "details": error.details
            }
        )
    
    elif isinstance(error, VideoUploadError):
        logger.error("YouTube upload failed",
                    exc_info=error,
                    video_id=error.video_id,
                    **error.details)
        return HTTPException(
            status_code=502,
            detail={
                "message": "Failed to upload video to YouTube",
                "video_id": error.video_id,
                "details": error.details
            }
        )
    
    elif isinstance(error, ProcessingTimeoutError):
        logger.error("Video processing timed out",
                    exc_info=error,
                    video_id=error.video_id,
                    **error.details)
        return HTTPException(
            status_code=408,
            detail={
                "message": "Video processing timed out",
                "video_id": error.video_id,
                "details": error.details
            }
        )
    
    elif isinstance(error, ValidationError):
        logger.error("Video validation failed",
                    exc_info=error,
                    video_id=error.video_id,
                    **error.details)
        return HTTPException(
            status_code=400,
            detail={
                "message": "Video validation failed",
                "video_id": error.video_id,
                "details": error.details
            }
        )
    
    # Handle unexpected errors
    logger.error("Unexpected error during video processing",
                exc_info=error)
    return HTTPException(
        status_code=500,
        detail={
            "message": "An unexpected error occurred",
            "error_type": error.__class__.__name__
        }
    )

def validate_video_format(file_extension: str, file_size: int, max_size: int = 100 * 1024 * 1024) -> None:
    """Validate video format and size."""
    allowed_extensions = {'.mp4', '.mov', '.avi'}
    
    if not any(file_extension.lower().endswith(ext) for ext in allowed_extensions):
        raise ValidationError(
            message="Invalid video format",
            details={
                "allowed_formats": list(allowed_extensions),
                "provided_format": file_extension
            }
        )
    
    if file_size > max_size:
        raise ValidationError(
            message="File size too large",
            details={
                "max_size_mb": max_size / (1024 * 1024),
                "file_size_mb": file_size / (1024 * 1024)
            }
        )

# Example usage:
# try:
#     validate_video_format('.txt', 1024 * 1024 * 200)
# except Exception as e:
#     error_handler = handle_processing_error(e, CustomLogger(api_logger))
#     # Handle the HTTP exception...