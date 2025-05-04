from celery import Celery
from services.video_processor import VideoProcessor
from services.youtube_uploader import YouTubeUploader
from models import Video
from sqlalchemy.orm import Session
from database import SessionLocal
import os

celery = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@celery.task
def process_video(video_id: int):
    """Process video with subtitle detection and generation."""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {'status': 'error', 'message': 'Video not found'}

        video.status = 'processing'
        db.commit()

        processor = VideoProcessor()
        try:
            processed_path, has_subtitles, subtitle_text = processor.process_video(video.file_path)
            
            video.processed_path = processed_path
            video.has_subtitles = has_subtitles
            video.subtitles_text = subtitle_text
            video.status = 'processed'
            db.commit()

            return {
                'status': 'success',
                'video_id': video_id,
                'processed_path': processed_path,
                'has_subtitles': has_subtitles
            }
        except Exception as e:
            video.status = 'failed'
            db.commit()
            raise e

    finally:
        db.close()

@celery.task
def upload_to_youtube(video_id: int, title: str = None, description: str = None, tags: list = None):
    """Upload processed video to YouTube as a Short."""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {'status': 'error', 'message': 'Video not found'}

        if not video.processed_path:
            return {'status': 'error', 'message': 'Video not processed yet'}

        uploader = YouTubeUploader()
        try:
            # Use video title or generate one based on niche if available
            video_title = title or f"#{video.niche.name if video.niche else 'shorts'}"
            
            # Upload to YouTube
            result = uploader.upload_video(
                file_path=video.processed_path,
                title=video_title,
                description=description or '',
                tags=tags or []
            )

            # Update video with YouTube URL
            video.youtube_url = result['url']
            db.commit()

            return {
                'status': 'success',
                'video_id': video_id,
                'youtube_url': result['url']
            }
        except Exception as e:
            video.status = 'upload_failed'
            db.commit()
            raise e

    finally:
        db.close()

@celery.task
def cleanup_video_files(video_id: int):
    """Clean up temporary video files after successful upload."""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {'status': 'error', 'message': 'Video not found'}

        # Only cleanup if video has been uploaded to YouTube
        if not video.youtube_url:
            return {'status': 'error', 'message': 'Video not uploaded yet'}

        # Remove original file
        if os.path.exists(video.file_path):
            os.remove(video.file_path)

        # Remove processed file
        if video.processed_path and os.path.exists(video.processed_path):
            os.remove(video.processed_path)

        return {'status': 'success', 'video_id': video_id}

    finally:
        db.close()