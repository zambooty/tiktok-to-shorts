import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Optional, Dict
import pickle
import time
from utils.logging_config import CustomLogger, youtube_logger
from utils.error_handling import VideoUploadError

class YouTubeUploader:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube'
        ]
        self.api_name = "youtube"
        self.api_version = "v3"
        self.client_secrets_file = "client_secrets.json"
        self.credentials_path = "token.pickle"
        self.youtube = None
        self.logger = CustomLogger(youtube_logger, {'component': 'youtube_uploader'})

    def authenticate(self) -> None:
        """Authenticate with YouTube API."""
        self.logger.info("Starting YouTube authentication")
        credentials = None

        try:
            # Load existing credentials if available
            if os.path.exists(self.credentials_path):
                with open(self.credentials_path, 'rb') as token:
                    credentials = pickle.load(token)

            # Refresh token if expired
            if credentials and credentials.expired and credentials.refresh_token:
                self.logger.info("Refreshing expired credentials")
                credentials.refresh(Request())
            
            # If no valid credentials available, authenticate user
            if not credentials or not credentials.valid:
                if not os.path.exists(self.client_secrets_file):
                    raise VideoUploadError(
                        message="Client secrets file not found",
                        details={"path": self.client_secrets_file}
                    )
                
                self.logger.info("Starting new authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes)
                credentials = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(self.credentials_path, 'wb') as token:
                    pickle.dump(credentials, token)

            self.youtube = build(
                self.api_name, 
                self.api_version, 
                credentials=credentials
            )
            self.logger.info("YouTube authentication successful")

        except Exception as e:
            self.logger.error(
                "YouTube authentication failed",
                exc_info=e
            )
            raise VideoUploadError(
                message="Failed to authenticate with YouTube",
                details={"error": str(e)}
            )

    def upload_video(self, 
                    file_path: str, 
                    title: str, 
                    description: Optional[str] = None,
                    tags: Optional[list] = None) -> Dict[str, str]:
        """Upload video to YouTube as a Short."""
        if not self.youtube:
            self.authenticate()

        self.logger.info(
            "Starting video upload",
            file_path=file_path,
            title=title
        )
        start_time = time.time()

        try:
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description or '',
                    'tags': tags or [],
                    'categoryId': '22'  # People & Blogs category
                },
                'status': {
                    'privacyStatus': 'private',  # Start as private, can be changed later
                    'selfDeclaredMadeForKids': False
                }
            }

            # Prepare media file
            media = MediaFileUpload(
                file_path,
                mimetype='video/*',
                resumable=True
            )

            # Execute upload request
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            # Upload the video with progress tracking
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    self.logger.info(
                        f"Upload progress: {progress}%",
                        progress=progress
                    )

            upload_time = time.time() - start_time
            video_id = response['id']
            video_url = f"https://youtube.com/shorts/{video_id}"

            self.logger.info(
                "Video upload completed",
                video_id=video_id,
                video_url=video_url,
                upload_time=upload_time
            )

            return {
                'id': video_id,
                'url': video_url
            }

        except Exception as e:
            self.logger.error(
                "Video upload failed",
                exc_info=e,
                file_path=file_path,
                title=title
            )
            raise VideoUploadError(
                message="Failed to upload video to YouTube",
                details={
                    "file_path": file_path,
                    "title": title,
                    "error": str(e)
                }
            )

    def update_video_privacy(self, video_id: str, privacy_status: str = 'public') -> None:
        """Update the privacy status of a video."""
        if not self.youtube:
            self.authenticate()

        self.logger.info(
            "Updating video privacy",
            video_id=video_id,
            privacy_status=privacy_status
        )

        try:
            self.youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {
                        "privacyStatus": privacy_status
                    }
                }
            ).execute()

            self.logger.info(
                "Video privacy updated successfully",
                video_id=video_id,
                privacy_status=privacy_status
            )

        except Exception as e:
            self.logger.error(
                "Failed to update video privacy",
                exc_info=e,
                video_id=video_id,
                privacy_status=privacy_status
            )
            raise VideoUploadError(
                message="Failed to update video privacy",
                details={
                    "video_id": video_id,
                    "privacy_status": privacy_status,
                    "error": str(e)
                }
            )

    def add_to_playlist(self, video_id: str, playlist_id: str) -> None:
        """Add a video to a specific playlist."""
        if not self.youtube:
            self.authenticate()

        self.logger.info(
            "Adding video to playlist",
            video_id=video_id,
            playlist_id=playlist_id
        )

        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()

            self.logger.info(
                "Video added to playlist successfully",
                video_id=video_id,
                playlist_id=playlist_id
            )

        except Exception as e:
            self.logger.error(
                "Failed to add video to playlist",
                exc_info=e,
                video_id=video_id,
                playlist_id=playlist_id
            )
            raise VideoUploadError(
                message="Failed to add video to playlist",
                details={
                    "video_id": video_id,
                    "playlist_id": playlist_id,
                    "error": str(e)
                }
            )

    def create_playlist(self, title: str, description: Optional[str] = None) -> str:
        """Create a new playlist and return its ID."""
        if not self.youtube:
            self.authenticate()

        self.logger.info(
            "Creating new playlist",
            title=title
        )

        try:
            playlist = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description or ""
                    },
                    "status": {
                        "privacyStatus": "private"
                    }
                }
            ).execute()

            playlist_id = playlist["id"]
            self.logger.info(
                "Playlist created successfully",
                playlist_id=playlist_id,
                title=title
            )

            return playlist_id

        except Exception as e:
            self.logger.error(
                "Failed to create playlist",
                exc_info=e,
                title=title
            )
            raise VideoUploadError(
                message="Failed to create playlist",
                details={
                    "title": title,
                    "error": str(e)
                }
            )