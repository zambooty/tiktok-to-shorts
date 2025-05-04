import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Optional, Dict
import pickle

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

    def authenticate(self) -> None:
        """Authenticate with YouTube API."""
        credentials = None

        # Load existing credentials if available
        if os.path.exists(self.credentials_path):
            with open(self.credentials_path, 'rb') as token:
                credentials = pickle.load(token)

        # Refresh token if expired
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        
        # If no valid credentials available, authenticate user
        if not credentials or not credentials.valid:
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

    def upload_video(self, 
                    file_path: str, 
                    title: str, 
                    description: Optional[str] = None,
                    tags: Optional[list] = None) -> Dict[str, str]:
        """Upload video to YouTube as a Short."""
        if not self.youtube:
            self.authenticate()

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

        try:
            # Execute upload request
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            # Upload the video
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")

            return {
                'id': response['id'],
                'url': f"https://youtube.com/shorts/{response['id']}"
            }

        except Exception as e:
            print(f"An error occurred: {e}")
            raise

    def update_video_privacy(self, video_id: str, privacy_status: str = 'public') -> None:
        """Update the privacy status of a video."""
        if not self.youtube:
            self.authenticate()

        self.youtube.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {
                    "privacyStatus": privacy_status
                }
            }
        ).execute()

    def add_to_playlist(self, video_id: str, playlist_id: str) -> None:
        """Add a video to a specific playlist."""
        if not self.youtube:
            self.authenticate()

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

    def create_playlist(self, title: str, description: Optional[str] = None) -> str:
        """Create a new playlist and return its ID."""
        if not self.youtube:
            self.authenticate()

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

        return playlist["id"]