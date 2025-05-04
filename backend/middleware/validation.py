from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import magic
from pathlib import Path
from utils.logging_config import CustomLogger, api_logger

logger = CustomLogger(api_logger, {'component': 'request_validator'})

class RequestValidator:
    def __init__(self):
        self.allowed_video_types = [
            'video/mp4',
            'video/quicktime',  # .mov
            'video/x-msvideo'   # .avi
        ]
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_file_extensions = {'.mp4', '.mov', '.avi'}

    async def validate_file_type(self, file_path: str) -> bool:
        """Validate file type using libmagic."""
        try:
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)
            return file_type in self.allowed_video_types
        except Exception as e:
            logger.error(
                "File type validation failed",
                exc_info=e,
                file_path=file_path
            )
            return False

    def validate_file_extension(self, filename: str) -> bool:
        """Validate file extension."""
        return Path(filename).suffix.lower() in self.allowed_file_extensions

    async def validate_video_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate video metadata."""
        errors = []
        required_fields = ['title']
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Missing required field: {field}")

        if 'title' in metadata and len(metadata['title']) > 100:
            errors.append("Title must be less than 100 characters")

        if 'description' in metadata and len(metadata['description']) > 5000:
            errors.append("Description must be less than 5000 characters")

        if 'tags' in metadata:
            if not isinstance(metadata['tags'], list):
                errors.append("Tags must be a list")
            elif len(metadata['tags']) > 500:
                errors.append("Too many tags (maximum 500)")

        return errors

    async def __call__(self, request: Request):
        """Validate incoming requests."""
        path = request.url.path
        method = request.method

        try:
            # Validate video upload requests
            if 'upload' in path and method == 'POST':
                form = await request.form()
                
                if 'file' not in form:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "No file uploaded"}
                    )

                file = form['file']
                
                # Validate file size
                if len(await file.read()) > self.max_file_size:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "File size exceeds maximum limit (100MB)"}
                    )
                await file.seek(0)  # Reset file pointer

                # Validate file extension
                if not self.validate_file_extension(file.filename):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "detail": "Invalid file type. Allowed extensions: .mp4, .mov, .avi"
                        }
                    )

            # Validate video processing requests
            elif 'process' in path and method == 'POST':
                body = await request.json()
                metadata_errors = await self.validate_video_metadata(body)
                
                if metadata_errors:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": metadata_errors}
                    )

            logger.info(
                "Request validation successful",
                path=path,
                method=method
            )

        except Exception as e:
            logger.error(
                "Request validation failed",
                exc_info=e,
                path=path,
                method=method
            )
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request"}
            )

        return None  # Allow request to proceed

class SecurityHeaders:
    """Add security headers to responses."""
    
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https:;"
        )
        
        return response