"""
Feedback collection system for tracking implicit and explicit user signals
to improve retrieval relevance over time.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

import structlog

logger = structlog.get_logger()


class FeedbackTracker:
    """Tracks search sessions and user relevance feedback."""

    def __init__(self, storage_dir: str = "feedback_db"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.metrics = {
            "total_queries": 0,
            "positive_feedback": 0,
            "negative_feedback": 0
        }

    def start_session(self, query: str, query_type: str = "text") -> str:
        """Start a new search session."""
        session_id = uuid.uuid4().hex[:12]
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "query_type": query_type,
            "results": [],
            "feedback": []
        }
        self._save_session(session_id, session_data)
        self.metrics["total_queries"] += 1
        return session_id

    def log_results(self, session_id: str, results: List[Dict[str, Any]]):
        """Log the retrieved results for a session."""
        session_data = self._load_session(session_id)
        if session_data:
            session_data["results"] = results
            self._save_session(session_id, session_data)

    def submit_feedback(self, session_id: str, item_id: str, is_relevant: bool, comment: str = ""):
        """Submit explicit user feedback on a specific result item."""
        session_data = self._load_session(session_id)
        if session_data:
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "item_id": item_id,
                "is_relevant": is_relevant,
                "comment": comment
            }
            session_data["feedback"].append(feedback_entry)
            self._save_session(session_id, session_data)
            
            if is_relevant:
                self.metrics["positive_feedback"] += 1
            else:
                self.metrics["negative_feedback"] += 1
                
            logger.info("feedback_received", session=session_id, item=item_id, relevant=is_relevant)

    def _get_filename(self, session_id: str) -> str:
        return os.path.join(self.storage_dir, f"session_{session_id}.json")

    def _save_session(self, session_id: str, data: dict):
        with open(self._get_filename(session_id), 'w') as f:
            json.dump(data, f, indent=2)

    def _load_session(self, session_id: str) -> Dict[str, Any]:
        filename = self._get_filename(session_id)
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None
        
    def get_metrics(self) -> dict:
        return self.metrics
