"""
Session Manager for Repo Rover API
Manages user sessions and pipeline state
"""
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock


class Session:
    """Represents a user session with pipeline state"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

        # Pipeline state
        self.rover_instance = None  # RepoRover instance
        self.paper_info = None      # Paper metadata
        self.repo_path = None        # Path to cloned repo
        self.is_initialized = False  # Pipeline ready for Q&A
        self.initialization_error = None  # Error during init

        # Paper selection state
        self.awaiting_paper_selection = False  # Waiting for user to select paper
        self.paper_options = None    # List of paper options to choose from
        self.original_query = None   # Original search query
        self.search_mode = "arxiv"   # "arxiv" or "gemini"

    def touch(self):
        """Update last accessed time"""
        self.last_accessed = datetime.now()

    def is_expired(self, max_age_hours: int = 2) -> bool:
        """Check if session has expired"""
        age = datetime.now() - self.last_accessed
        return age > timedelta(hours=max_age_hours)


class SessionManager:
    """Thread-safe session manager"""

    def __init__(self, max_age_hours: int = 2):
        self.sessions: Dict[str, Session] = {}
        self.lock = Lock()
        self.max_age_hours = max_age_hours

    def create_session(self) -> str:
        """
        Create a new session

        Returns:
            Session ID
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = Session(session_id)
            return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found/expired
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if not session:
                return None

            if session.is_expired(self.max_age_hours):
                # Clean up expired session
                del self.sessions[session_id]
                return None

            session.touch()
            return session

    def update_session(self, session_id: str, **kwargs):
        """
        Update session attributes

        Args:
            session_id: Session ID
            **kwargs: Attributes to update
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                session.touch()

    def delete_session(self, session_id: str):
        """Delete a session"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]

    def cleanup_expired(self):
        """Remove all expired sessions"""
        with self.lock:
            expired = [
                sid for sid, session in self.sessions.items()
                if session.is_expired(self.max_age_hours)
            ]
            for sid in expired:
                del self.sessions[sid]
            return len(expired)

    def get_session_count(self) -> int:
        """Get number of active sessions"""
        with self.lock:
            return len(self.sessions)
