import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """Function to setup a custom logger."""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    handler = RotatingFileHandler(
        logs_dir / log_file,
        maxBytes=10000000,  # 10MB
        backupCount=5
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # Add console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Setup different loggers for different components
video_logger = setup_logger('video_processing', 'video_processing.log')
youtube_logger = setup_logger('youtube_upload', 'youtube_upload.log')
api_logger = setup_logger('api', 'api.log')

class CustomLogger:
    """Custom logger class with context information."""
    
    def __init__(self, logger: logging.Logger, context: dict = None):
        self.logger = logger
        self.context = context or {}
    
    def _format_message(self, message: str) -> str:
        if self.context:
            context_str = ' '.join(f'{k}={v}' for k, v in self.context.items())
            return f'{message} - {context_str}'
        return message
    
    def info(self, message: str, **kwargs):
        """Log info message with optional additional context."""
        context = {**self.context, **kwargs}
        self.logger.info(self._format_message(message), extra=context)
    
    def error(self, message: str, exc_info=None, **kwargs):
        """Log error message with optional exception info and context."""
        context = {**self.context, **kwargs}
        self.logger.error(self._format_message(message), exc_info=exc_info, extra=context)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        context = {**self.context, **kwargs}
        self.logger.warning(self._format_message(message), extra=context)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        context = {**self.context, **kwargs}
        self.logger.debug(self._format_message(message), extra=context)

# Example usage:
# video_processing_logger = CustomLogger(video_logger, {'component': 'video_processor'})
# video_processing_logger.info('Started processing video', video_id='123', format='mp4')