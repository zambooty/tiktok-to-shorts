from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logging_config import CustomLogger, api_logger

router = APIRouter()
logger = CustomLogger(api_logger, {'component': 'error_handler'})

class ErrorReport(BaseModel):
    error: Dict[str, Any]
    errorInfo: Optional[str] = None
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None

@router.post("/api/errors/log")
async def log_client_error(error_report: ErrorReport):
    """Log client-side errors."""
    try:
        # Extract error details
        error_name = error_report.error.get('name', 'Unknown Error')
        error_message = error_report.error.get('message', 'No message provided')
        error_stack = error_report.error.get('stack', 'No stack trace')

        # Log the error with all available context
        logger.error(
            f"Client Error: {error_name}",
            exc_info=False,
            error_message=error_message,
            error_stack=error_stack,
            component_stack=error_report.errorInfo,
            client_timestamp=error_report.timestamp,
            additional_context=error_report.context
        )

        return {"status": "error logged"}

    except Exception as e:
        logger.error(
            "Failed to log client error",
            exc_info=e,
            error_report=error_report.dict()
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to log error"
        )

@router.get("/api/errors/recent")
async def get_recent_errors():
    """Get recent error logs for the admin dashboard."""
    try:
        # In a real implementation, you would fetch this from your logging system
        # For now, we'll return a placeholder response
        return {
            "status": "success",
            "message": "Error log retrieval not implemented yet"
        }
    except Exception as e:
        logger.error("Failed to retrieve error logs", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve error logs"
        )