from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Video, Niche
from datetime import datetime, timedelta
from typing import List
from services.youtube_uploader import YouTubeUploader

router = APIRouter()

@router.get("/api/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overall statistics for the dashboard."""
    total_videos = db.query(func.count(Video.id)).scalar()
    processed_videos = db.query(func.count(Video.id)).filter(
        Video.status == "processed"
    ).scalar()
    total_niches = db.query(func.count(Niche.id)).scalar()
    
    # Calculate average processing time
    processed_videos_with_time = db.query(Video).filter(
        Video.status == "processed"
    ).all()
    
    total_processing_time = 0
    video_count = 0
    
    for video in processed_videos_with_time:
        if video.created_at:
            processing_time = (datetime.utcnow() - video.created_at).total_seconds()
            total_processing_time += processing_time
            video_count += 1
    
    avg_processing_time = (
        total_processing_time / video_count if video_count > 0 else 0
    )
    
    return {
        "totalVideos": total_videos,
        "processedVideos": processed_videos,
        "totalNiches": total_niches,
        "averageProcessingTime": round(avg_processing_time, 2)
    }

@router.get("/api/videos/recent")
async def get_recent_videos(db: Session = Depends(get_db)):
    """Get recent videos with their stats."""
    videos = db.query(Video).order_by(Video.created_at.desc()).limit(10).all()
    
    # Initialize YouTube API client
    youtube = YouTubeUploader()
    
    video_stats = []
    for video in videos:
        stats = {
            "id": video.id,
            "title": video.title,
            "status": video.status,
            "niche": video.niche.name if video.niche else "Uncategorized",
            "youtubeUrl": video.youtube_url,
            "processedAt": video.created_at.isoformat(),
            "views": None,
            "likes": None
        }
        
        # If video is uploaded to YouTube, fetch its statistics
        if video.youtube_url and youtube.youtube:
            try:
                video_id = video.youtube_url.split("/")[-1]
                response = youtube.youtube.videos().list(
                    part="statistics",
                    id=video_id
                ).execute()
                
                if response["items"]:
                    statistics = response["items"][0]["statistics"]
                    stats["views"] = int(statistics.get("viewCount", 0))
                    stats["likes"] = int(statistics.get("likeCount", 0))
            except Exception as e:
                print(f"Error fetching YouTube stats for video {video.id}: {e}")
        
        video_stats.append(stats)
    
    return video_stats

@router.get("/api/stats/niche-performance")
async def get_niche_performance(db: Session = Depends(get_db)):
    """Get performance statistics by niche."""
    niches = db.query(Niche).all()
    
    niche_stats = []
    for niche in niches:
        total_videos = db.query(func.count(Video.id)).filter(
            Video.niche_id == niche.id
        ).scalar()
        
        successful_uploads = db.query(func.count(Video.id)).filter(
            Video.niche_id == niche.id,
            Video.youtube_url.isnot(None)
        ).scalar()
        
        success_rate = (successful_uploads / total_videos * 100) if total_videos > 0 else 0
        
        niche_stats.append({
            "nicheName": niche.name,
            "totalVideos": total_videos,
            "successfulUploads": successful_uploads,
            "successRate": round(success_rate, 2)
        })
    
    return niche_stats

@router.get("/api/stats/processing-history")
async def get_processing_history(days: int = 7, db: Session = Depends(get_db)):
    """Get video processing history over time."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    videos = db.query(
        func.date(Video.created_at).label('date'),
        func.count(Video.id).label('count')
    ).filter(
        Video.created_at >= start_date
    ).group_by(
        func.date(Video.created_at)
    ).all()
    
    history = [
        {
            "date": str(video.date),
            "count": video.count
        }
        for video in videos
    ]
    
    return history