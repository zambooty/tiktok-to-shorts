import cv2
import pytesseract
import whisper
import ffmpeg
import os
from typing import Tuple, Optional
from pathlib import Path
import time
from utils.logging_config import CustomLogger, video_logger
from utils.error_handling import (
    SubtitleDetectionError,
    ProcessingTimeoutError,
    VideoProcessingError
)

class VideoProcessor:
    def __init__(self, upload_dir: str = "uploads", processed_dir: str = "processed"):
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.model = whisper.load_model("base")
        self.logger = CustomLogger(video_logger, {'component': 'video_processor'})
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)

    def detect_subtitles(self, video_path: str, max_frames: int = 10) -> bool:
        """Detect if video already has subtitles using OCR."""
        self.logger.info("Starting subtitle detection", video_path=video_path)
        start_time = time.time()
        
        cap = cv2.VideoCapture(video_path)
        has_subtitles = False
        frames_checked = 0
        
        try:
            for i in range(max_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                
                frames_checked += 1
                # Focus on bottom third of frame where subtitles usually appear
                height = frame.shape[0]
                subtitle_region = frame[height//2:, :]
                
                # Convert to grayscale for better OCR
                gray = cv2.cvtColor(subtitle_region, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray)
                
                if len(text.strip()) > 0:
                    has_subtitles = True
                    break

            processing_time = time.time() - start_time
            self.logger.info(
                "Subtitle detection completed",
                video_path=video_path,
                has_subtitles=has_subtitles,
                frames_checked=frames_checked,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(
                "Subtitle detection failed",
                exc_info=e,
                video_path=video_path
            )
            raise SubtitleDetectionError(
                message="Failed to detect subtitles",
                details={
                    "video_path": video_path,
                    "error": str(e)
                }
            )
        finally:
            cap.release()
            
        return has_subtitles

    def generate_subtitles(self, video_path: str) -> Tuple[str, str]:
        """Generate subtitles using Whisper and return subtitle text and SRT path."""
        self.logger.info("Starting subtitle generation", video_path=video_path)
        start_time = time.time()
        
        try:
            # Transcribe audio
            result = self.model.transcribe(video_path)
            
            # Create SRT file
            base_path = Path(video_path).stem
            srt_path = self.processed_dir / f"{base_path}.srt"
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result["segments"], 1):
                    start = self._format_timestamp(segment["start"])
                    end = self._format_timestamp(segment["end"])
                    text = segment["text"].strip()
                    
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")

            processing_time = time.time() - start_time
            self.logger.info(
                "Subtitle generation completed",
                video_path=video_path,
                srt_path=str(srt_path),
                processing_time=processing_time
            )
            
            return result["text"], str(srt_path)
            
        except Exception as e:
            self.logger.error(
                "Subtitle generation failed",
                exc_info=e,
                video_path=video_path
            )
            raise VideoProcessingError(
                message="Failed to generate subtitles",
                details={
                    "video_path": video_path,
                    "error": str(e)
                }
            )

    def overlay_subtitles(self, video_path: str, srt_path: str) -> str:
        """Overlay subtitles on video using FFmpeg."""
        self.logger.info(
            "Starting subtitle overlay",
            video_path=video_path,
            srt_path=srt_path
        )
        start_time = time.time()
        
        output_path = self.processed_dir / f"{Path(video_path).stem}_subtitled.mp4"
        
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.filter(stream, 'subtitles', str(srt_path))
            stream = ffmpeg.output(stream, str(output_path))
            ffmpeg.run(stream, overwrite_output=True)
            
            processing_time = time.time() - start_time
            self.logger.info(
                "Subtitle overlay completed",
                video_path=video_path,
                output_path=str(output_path),
                processing_time=processing_time
            )
            
            return str(output_path)
            
        except ffmpeg.Error as e:
            self.logger.error(
                "Subtitle overlay failed",
                exc_info=e,
                video_path=video_path,
                srt_path=srt_path,
                error_stdout=e.stdout.decode() if e.stdout else None,
                error_stderr=e.stderr.decode() if e.stderr else None
            )
            raise VideoProcessingError(
                message="Failed to overlay subtitles",
                details={
                    "video_path": video_path,
                    "srt_path": srt_path,
                    "error": e.stderr.decode() if e.stderr else str(e)
                }
            )

    def process_video(self, video_path: str, max_processing_time: int = 300) -> Tuple[str, bool, Optional[str]]:
        """Main processing function that handles subtitle detection and generation."""
        start_time = time.time()
        self.logger.info("Starting video processing", video_path=video_path)
        
        try:
            has_subtitles = self.detect_subtitles(video_path)
            subtitle_text = None
            processed_path = video_path
            
            if not has_subtitles:
                # Generate and overlay subtitles
                subtitle_text, srt_path = self.generate_subtitles(video_path)
                processed_path = self.overlay_subtitles(video_path, srt_path)
                has_subtitles = True
            
            processing_time = time.time() - start_time
            if processing_time > max_processing_time:
                raise ProcessingTimeoutError(
                    message="Video processing exceeded maximum time limit",
                    details={
                        "video_path": video_path,
                        "processing_time": processing_time,
                        "max_processing_time": max_processing_time
                    }
                )
            
            self.logger.info(
                "Video processing completed",
                video_path=video_path,
                processed_path=processed_path,
                has_subtitles=has_subtitles,
                processing_time=processing_time
            )
            
            return processed_path, has_subtitles, subtitle_text
            
        except Exception as e:
            self.logger.error(
                "Video processing failed",
                exc_info=e,
                video_path=video_path
            )
            raise

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"