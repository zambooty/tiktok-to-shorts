from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import shutil
import json
from pathlib import Path
from config import Settings, get_settings
import os

router = APIRouter()

class SettingsUpdate(BaseModel):
    subtitleFontSize: Optional[int] = None
    subtitleFontColor: Optional[str] = None
    subtitleBackground: Optional[bool] = None
    subtitlePosition: Optional[str] = None
    checkSubtitleFrames: Optional[int] = None

@router.get("/api/settings")
async def get_settings_config(settings: Settings = Depends(get_settings)):
    """Get current application settings."""
    client_secrets_exists = os.path.exists(settings.YOUTUBE_CLIENT_SECRETS_FILE)
    
    return {
        "youtubeClientSecretsFile": settings.YOUTUBE_CLIENT_SECRETS_FILE if client_secrets_exists else "",
        "subtitleFontSize": settings.SUBTITLE_FONT_SIZE,
        "subtitleFontColor": settings.SUBTITLE_FONT_COLOR,
        "subtitleBackground": settings.SUBTITLE_BACKGROUND,
        "subtitlePosition": settings.SUBTITLE_POSITION,
        "checkSubtitleFrames": settings.CHECK_SUBTITLE_FRAMES
    }

@router.post("/api/settings")
async def update_settings(
    client_secrets: Optional[UploadFile] = File(None),
    settings_update: SettingsUpdate = Depends(),
    settings: Settings = Depends(get_settings)
):
    """Update application settings."""
    try:
        # Handle client secrets file upload
        if client_secrets:
            try:
                # Validate JSON format
                content = await client_secrets.read()
                json.loads(content)
                
                # Save the file
                with open(settings.YOUTUBE_CLIENT_SECRETS_FILE, "wb") as f:
                    await client_secrets.seek(0)
                    shutil.copyfileobj(client_secrets.file, f)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid client secrets file format"
                )
        
        # Update settings in .env file
        env_path = Path(".env")
        env_settings = {}
        
        # Read existing settings
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        env_settings[key] = value

        # Update with new values
        if settings_update.subtitleFontSize is not None:
            env_settings["SUBTITLE_FONT_SIZE"] = str(settings_update.subtitleFontSize)
        if settings_update.subtitleFontColor is not None:
            env_settings["SUBTITLE_FONT_COLOR"] = settings_update.subtitleFontColor
        if settings_update.subtitleBackground is not None:
            env_settings["SUBTITLE_BACKGROUND"] = str(settings_update.subtitleBackground)
        if settings_update.subtitlePosition is not None:
            env_settings["SUBTITLE_POSITION"] = settings_update.subtitlePosition
        if settings_update.checkSubtitleFrames is not None:
            env_settings["CHECK_SUBTITLE_FRAMES"] = str(settings_update.checkSubtitleFrames)

        # Write updated settings
        with open(env_path, "w") as f:
            for key, value in env_settings.items():
                f.write(f"{key}={value}\n")

        return {"status": "success", "message": "Settings updated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating settings: {str(e)}"
        )