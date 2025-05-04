from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    file_path = Column(String)
    processed_path = Column(String, nullable=True)
    has_subtitles = Column(Boolean, default=False)
    status = Column(String)  # 'uploaded', 'processing', 'processed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=True)
    youtube_url = Column(String, nullable=True)
    subtitles_text = Column(Text, nullable=True)

    niche = relationship("Niche", back_populates="videos")

class Niche(Base):
    __tablename__ = "niches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    videos = relationship("Video", back_populates="niche")
