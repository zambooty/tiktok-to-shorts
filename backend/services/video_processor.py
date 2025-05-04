import cv2
import pytesseract
import whisper
import ffmpeg
import os
from typing import Tuple, Optional
from pathlib import Path

class VideoProcessor:
    def __init__(self, upload_dir: str = "uploads", processed_dir: str = "processed"):
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.model = whisper.load_model("base")
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)

    def detect_subtitles(self, video_path: str) -> bool:
        """Detect if video already has subtitles using OCR."""
        cap = cv2.VideoCapture(video_path)
        has_subtitles = False
        frames_to_check = 10  # Check first 10 frames
        
        try:
            for i in range(frames_to_check):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Focus on bottom third of frame where subtitles usually appear
                height = frame.shape[0]
                subtitle_region = frame[height//2:, :]
                
                # Convert to grayscale for better OCR
                gray = cv2.cvtColor(subtitle_region, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray)
                
                if len(text.strip()) > 0:
                    has_subtitles = True
                    break
        finally:
            cap.release()
            
        return has_subtitles

    def generate_subtitles(self, video_path: str) -> Tuple[str, str]:
        """Generate subtitles using Whisper and return subtitle text and SRT path."""
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
        
        return result["text"], str(srt_path)

    def overlay_subtitles(self, video_path: str, srt_path: str) -> str:
        """Overlay subtitles on video using FFmpeg."""
        output_path = self.processed_dir / f"{Path(video_path).stem}_subtitled.mp4"
        
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.filter(stream, 'subtitles', str(srt_path))
            stream = ffmpeg.output(stream, str(output_path))
            ffmpeg.run(stream, overwrite_output=True)
        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise
            
        return str(output_path)

    def process_video(self, video_path: str) -> Tuple[str, bool, Optional[str]]:
        """Main processing function that handles subtitle detection and generation."""
        has_subtitles = self.detect_subtitles(video_path)
        subtitle_text = None
        processed_path = video_path
        
        if not has_subtitles:
            # Generate and overlay subtitles
            subtitle_text, srt_path = self.generate_subtitles(video_path)
            processed_path = self.overlay_subtitles(video_path, srt_path)
            has_subtitles = True
            
        return processed_path, has_subtitles, subtitle_text

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds % 1) * 1000)
        seconds = int(seconds)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"