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
    - Includes user context (HWID, license, version)
    """
    
    def __init__(self):
        """Initialize feedback service."""
        self._supabase = None
        self._config = ConfigManager()
        self.last_error: Optional[str] = None
        
    def _ensure_supabase(self):
        """Ensure Supabase client is initialized."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
    
    def submit_feedback(
        self,
        feedback_type: str,
        title: str,
        description: str,
        email: Optional[str] = None,
        customer_name: Optional[str] = None
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
            self.last_error = None
            self._ensure_supabase()

            # Normalize feedback type to schema
            if feedback_type == "feedback":
                feedback_type = "general"
            
            # Get user context
            from services.license_service import get_license_service
            license_service = get_license_service()
            
            hwid = get_hwid()
            license_info = license_service.get_license_info()
            license_key = license_info.get("license_key") or "Unknown"
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
            if customer_name:
                feedback_data["customer_name"] = customer_name
            
            # 1. Store in Supabase via RPC to avoid RLS insert failures
            result = self._supabase.rpc(
                "submit_feedback",
                {
                    "_type": feedback_data["type"],
                    "_title": feedback_data["title"],
                    "_description": feedback_data["description"],
                    "_email": feedback_data.get("email"),
                    "_customer_name": feedback_data.get("customer_name"),
                    "_hwid": feedback_data.get("hwid"),
                    "_license_key": feedback_data.get("license_key"),
                    "_app_version": feedback_data.get("app_version"),
                }
            )
            
            if not result:
                logger.error("Failed to insert feedback into Supabase")
                self.last_error = "Feedback was not accepted by the server."
                return False
            
            logger.info(f"Feedback stored in Supabase: {title}")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error submitting feedback: {e}")
            self.last_error = str(e)
            return False
    
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
