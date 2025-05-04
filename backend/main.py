from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime
from pathlib import Path

from database import get_db, engine
import models
from tasks import process_video, upload_to_youtube, cleanup_video_files

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directories exist
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

@app.post("/api/videos/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a new video for processing."""
    if not file.filename.endswith(('.mp4', '.mov', '.avi')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create video record
    db_video = models.Video(
        title=file.filename,
        file_path=str(file_path),
        status="uploaded"
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    # Start processing task
    process_video.delay(db_video.id)
    
    return {"id": db_video.id, "status": "processing"}

@app.get("/api/videos/processed")
def get_processed_videos(db: Session = Depends(get_db)):
    """Get list of processed videos."""
    videos = db.query(models.Video).filter(
        models.Video.status == "processed"
    ).all()
    return videos

@app.post("/api/videos/{video_id}/save")
def save_video(video_id: int, niche_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Save a video to a niche collection and trigger YouTube upload."""
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if niche_id:
        niche = db.query(models.Niche).filter(models.Niche.id == niche_id).first()
        if not niche:
            raise HTTPException(status_code=404, detail="Niche not found")
        video.niche_id = niche_id
    
    # Trigger YouTube upload
    upload_to_youtube.delay(video.id)
    
    db.commit()
    return {"status": "uploading to YouTube"}

@app.post("/api/videos/{video_id}/discard")
def discard_video(video_id: int, db: Session = Depends(get_db)):
    """Discard a video and clean up its files."""
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Trigger cleanup
    cleanup_video_files.delay(video.id)
    
    # Delete from database
    db.delete(video)
    db.commit()
    
    return {"status": "deleted"}

@app.get("/api/niches")
def get_niches(db: Session = Depends(get_db)):
    """Get all available niches."""
    niches = db.query(models.Niche).all()
    return niches

@app.post("/api/niches")
def create_niche(name: str, description: Optional[str] = None, db: Session = Depends(get_db)):
    """Create a new niche category."""
    db_niche = models.Niche(name=name, description=description)
    db.add(db_niche)
    db.commit()
    db.refresh(db_niche)
    return db_niche

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)