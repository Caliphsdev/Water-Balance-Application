"""
Feedback Service

Handles bug reports, feature requests, and general feedback submissions.
Implements hybrid approach: Supabase storage + email notification.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from core.hwid import get_hwid
from core.supabase_client import get_supabase_client
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


# (CONSTANTS)

# Company email for feedback notifications
FEEDBACK_EMAIL = "feedback@tworiversplatinum.com"  # Update with your actual email

# Feedback types
FEEDBACK_TYPES = {
    "bug": "🐛 Bug Report",
    "feature": "💡 Feature Request",
    "general": "📝 General Feedback"
}


# (FEEDBACK SERVICE)

class FeedbackService:
    """
    Service for submitting user feedback with hybrid storage approach.
    
    Features:
    - Submits to Supabase feature_requests table
    - Sends email notification to company
    - Includes user context (HWID, license, version)
    """
    
    def __init__(self):
        """Initialize feedback service."""
        self._supabase = None
        self._config = ConfigManager()
        
    def _ensure_supabase(self):
        """Ensure Supabase client is initialized."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
    
    def submit_feedback(
        self,
        feedback_type: str,
        title: str,
        description: str,
        email: Optional[str] = None
    ) -> bool:
        """
        Submit feedback to Supabase and send email notification.
        
        Args:
            feedback_type: Type of feedback ("bug", "feature", "feedback")
            title: Feedback title
            description: Detailed description
            email: Optional user email for follow-up
            
        Returns:
            True if submission succeeded, False otherwise
        """
        try:
            self._ensure_supabase()

            # Normalize feedback type to schema
            if feedback_type == "feedback":
                feedback_type = "general"
            
            # Get user context
            from services.license_service import get_license_service
            license_service = get_license_service()
            
            hwid = get_hwid()
            license_key = license_service.get_license_key() or "Unknown"
            app_version = self._config.get('app.version', '1.0.0')
            
            # Prepare feedback data
            feedback_data = {
                "type": feedback_type,
                "title": title,
                "description": description,
                "hwid": hwid,
                "license_key": license_key,
                "app_version": app_version,
                "status": "open",
                "created_at": datetime.utcnow().isoformat()
            }
            
            if email:
                feedback_data["email"] = email
            
            # 1. Store in Supabase
            result = self._supabase.insert("feature_requests", feedback_data)
            
            if not result:
                logger.error("Failed to insert feedback into Supabase")
                return False
            
            logger.info(f"Feedback stored in Supabase: {title}")
            
            # 2. Send email notification (disabled - set up later)
            # TODO: Enable email notifications when ready
            # self._send_email_notification(
            #     feedback_type=feedback_type,
            #     title=title,
            #     description=description,
            #     email=email,
            #     hwid=hwid,
            #     license_key=license_key,
            #     app_version=app_version
            # )
            
            return True
            
        except Exception as e:
            logger.exception(f"Error submitting feedback: {e}")
            return False
    
    def _send_email_notification(
        self,
        feedback_type: str,
        title: str,
        description: str,
        email: Optional[str],
        hwid: str,
        license_key: str,
        app_version: str
    ) -> None:
        """
        Send email notification about new feedback.
        
        Uses Supabase Edge Function for email delivery.
        Falls back gracefully if email fails.
        """
        try:
            # Format email body
            type_label = FEEDBACK_TYPES.get(feedback_type, "Feedback")
            
            email_body = f"""
New {type_label} Received
{'=' * 50}

Title: {title}

Type: {type_label}

Description:
{description}

{'=' * 50}
User Information:
- App Version: {app_version}
- License Key: {license_key}
- Hardware ID: {hwid}
"""
            
            if email:
                email_body += f"- User Email: {email}\n"
            
            email_body += f"\n{'=' * 50}\n"
            email_body += f"Submitted: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            
            # Prepare email data for Supabase Edge Function
            email_data = {
                "to": FEEDBACK_EMAIL,
                "subject": f"[Water Balance] {type_label}: {title}",
                "body": email_body,
                "from_app": "Water Balance Dashboard",
                "app_version": app_version
            }
            
            # Call Supabase Edge Function for email
            # Note: You'll need to create this function in Supabase
            # For now, we'll use the RPC method if available
            try:
                self._supabase._client.rpc('send_feedback_email', email_data).execute()
                logger.info(f"Email notification sent for feedback: {title}")
            except Exception as email_err:
                # Email is optional - don't fail if it doesn't work
                logger.warning(f"Email notification failed (non-critical): {email_err}")
                
        except Exception as e:
            # Don't fail the whole submission if email fails
            logger.warning(f"Failed to send email notification: {e}")


# (SINGLETON)

_service_instance: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """
    Get the singleton feedback service instance.
    
    Returns:
        FeedbackService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = FeedbackService()
    return _service_instance
