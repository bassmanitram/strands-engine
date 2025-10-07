"""
A session proxy that implements the SessionManager protocol to allow for dynamic
session switching.
"""
from typing import Optional, List, Any
from pathlib import Path
from loguru import logger
import shutil

from strands import Agent
from strands.session.session_manager import SessionManager
from strands.session.file_session_manager import FileSessionManager
from strands.types.content import Message


class DelegatingSession(SessionManager):
    """
    A session proxy that holds a real, switchable FileSessionManager object internally.
    This allows the active session to be changed mid-flight. It adheres to the
    SessionManager interface, making it compatible with the strands.Agent.
    """

    def __init__(self, session_name: Optional[str], sessions_home: Optional[str | Path] = None):
        """Initializes the proxy, optionally setting the first active session."""
        # Use default sessions_home if not provided - .strands-sessions in CWD
        default_home = Path.cwd() / ".strands-sessions"
        self._sessions_home = Path(sessions_home or default_home)
        
        self._active_session: Optional[FileSessionManager] = None  # FileSessionManager instance when active
        self._agent: Optional[Agent] = None  # strands-agents Agent instance
        self.session_id = session_name or "inactive"
        
        # Initialize parent SessionManager with session_id
        super().__init__(session_id=self.session_id)
        
        # Ensure sessions directory exists
        self._sessions_home.mkdir(parents=True, exist_ok=True)
        
        if session_name:
            logger.info(f"DelegatingSession configured for session '{session_name}' (will activate when agent available)")
            logger.debug(f"Sessions stored in: {self._sessions_home}")
        else:
            logger.info("DelegatingSession configured as inactive (will ignore session operations)")
            logger.debug(f"Sessions home available at: {self._sessions_home}")

    def set_active_session(self, session_name: str) -> None:
        """
        Creates and activates a new FileSessionManager. It then calls the new
        session's initialize() method to sync its history with the agent.
        Handles conversation manager type changes gracefully.
        """
        if not self._agent:
            logger.error("Cannot set active session: DelegatingSession has not been initialized with an agent yet.")
            return

        logger.info(f"Switching active session to '{session_name}'...")
        self.session_id = session_name

        new_session = FileSessionManager(session_id=session_name, storage_dir=str(self._sessions_home))

        # Try to initialize the session, but handle conversation manager state conflicts
        try:
            new_session.initialize(self._agent)
        except ValueError as e:
            if "Invalid conversation manager state" in str(e):
                logger.warning(f"Session '{session_name}' has incompatible conversation manager state.")
                logger.info("This can happen when switching between conversation manager types (e.g., sliding_window <-> summarizing).")
                logger.info("Creating a new session to avoid conflicts...")

                # Clear any existing session data and start fresh
                session_path = Path(self._sessions_home) / f"session_{session_name}"
                if session_path.exists():
                    logger.debug(f"Backing up incompatible session data to {session_path}.backup")
                    backup_path = Path(str(session_path) + ".backup")
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                    session_path.rename(backup_path)

                # Create a fresh session
                new_session = FileSessionManager(session_id=session_name, storage_dir=str(self._sessions_home))
                new_session.initialize(self._agent)
                logger.info(f"Created fresh session '{session_name}' with current conversation manager type.")
            else:
                # Re-raise other ValueError types
                raise
        except Exception as e:
            logger.error(f"Failed to initialize session '{session_name}': {e}")
            logger.info("Continuing without persistent session...")
            return

        self._active_session = new_session
        logger.info(f"DelegatingSession is now active for session_id: '{self.session_id}'. Agent history has been updated.")

    def deactivate_session(self) -> None:
        """Deactivate the current session, making the proxy inactive."""
        if self._active_session:
            logger.info(f"Deactivating session '{self.session_id}'")
            # Cleanup if needed
            if hasattr(self._active_session, 'cleanup'):
                try:
                    self._active_session.cleanup()
                except Exception as e:
                    logger.warning(f"Error during session cleanup: {e}")
            self._active_session = None
            self.session_id = "inactive"
        else:
            logger.debug("No active session to deactivate")

    def list_sessions(self) -> List[str]:
        """Scans the sessions directory and returns a list of available session names."""
        if not self._sessions_home.exists():
            return []

        # FileSessionManager saves files in folders named "session_<name>"
        try:
            session_dirs = [p for p in self._sessions_home.iterdir() if p.is_dir() and p.name.startswith("session_")]
            session_names = [p.name[len("session_"):] for p in session_dirs]
            return sorted(session_names)
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    @property
    def is_active(self) -> bool:
        """Returns True if a session is currently active."""
        return self._active_session is not None

    @property
    def current_session_id(self) -> Optional[str]:
        """Returns the current session ID, or None if inactive."""
        return self.session_id if self.is_active else None

    # --- Methods that implement the SessionManager abstract interface ---

    def initialize(self, agent: Agent, **kwargs: Any) -> None:
        """Stores the agent instance and sets up the initial session if one was provided."""
        self._agent = agent
        if self.session_id != "inactive" and not self._active_session:
            self.set_active_session(self.session_id)
        
        logger.info(f"DelegatingSession initialized with agent (active: {self.is_active})")

    def append_message(self, message: Message, agent: Agent, **kwargs: Any) -> None:
        """Appends a single message to the active session."""
        if self._active_session:
            self._active_session.append_message(message, agent, **kwargs)
            logger.debug(f"Appended message to session '{self.session_id}'")
        else:
            logger.debug("Session inactive - ignoring message append")

    def redact_latest_message(self, redact_message: Message, agent: Agent, **kwargs: Any) -> None:
        """Redacts the latest message from the active session."""
        if self._active_session:
            self._active_session.redact_latest_message(redact_message, agent, **kwargs)
            logger.debug(f"Redacted latest message in session '{self.session_id}'")
        else:
            logger.debug("Session inactive - ignoring message redaction")

    def sync_agent(self, agent: Agent) -> None:
        """Syncs the agent's state with the active session."""
        if self._active_session:
            self._active_session.sync_agent(agent)
            logger.debug(f"Synced agent state with session '{self.session_id}'")
        else:
            logger.debug("Session inactive - ignoring agent sync")

    def clear(self) -> None:
        """
        Clears the agent's in-memory messages. If a session is active,
        it also clears the persisted session file by overwriting it with an
        empty history, keeping the session active.
        """
        # Step 1: Always clear the agent's in-memory message list.
        if self._agent and hasattr(self._agent, 'messages') and self._agent.messages:
            self._agent.messages.clear()
            logger.debug("Cleared agent's in-memory message list.")

        # Step 2: If a session is active, clear its persisted file data
        # 
        # Note: Following YACBA's pattern - this is commented out as it may
        # delete important session data. Consider if we want to enable this.
        #
        # if self._active_session:
        #     # Clear the persisted session file by saving empty history
        #     self._active_session._save([])
        #     logger.info(f"Cleared session file for '{self.session_id}'. Session remains active.")
        
        if self._active_session:
            logger.info(f"Cleared agent memory. Session '{self.session_id}' remains active with persisted data intact.")
        else:
            logger.debug("Session inactive - no persistent data to clear")

    # --- Additional utility methods ---

    def save(self) -> None:
        """Force save current session state (if active)."""
        if self._active_session:
            try:
                # Force save session state
                if hasattr(self._active_session, 'save'):
                    self._active_session.save()
                elif hasattr(self._active_session, '_save'):
                    # Use private save method if public one not available
                    self._active_session._save(self._agent.messages if self._agent else [])
                logger.info(f"Manually saved session '{self.session_id}'")
            except Exception as e:
                logger.error(f"Error saving session '{self.session_id}': {e}")
        else:
            logger.debug("Session inactive - no data to save")

    def load(self, session_id: str) -> bool:
        """
        Load an existing session by ID.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            True if session was loaded successfully, False otherwise
        """
        try:
            if session_id in self.list_sessions():
                if self._active_session:
                    self.deactivate_session()
                
                self.set_active_session(session_id)
                return self.is_active
            else:
                logger.warning(f"Session '{session_id}' not found in {self._sessions_home}")
                return False
        except Exception as e:
            logger.error(f"Error loading session '{session_id}': {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if session was deleted successfully, False otherwise
        """
        try:
            # Deactivate if this is the current session
            if self.session_id == session_id:
                self.deactivate_session()
            
            # Delete session directory
            session_path = self._sessions_home / f"session_{session_id}"
            if session_path.exists():
                if session_path.is_dir():
                    shutil.rmtree(session_path)
                else:
                    session_path.unlink()
                logger.info(f"Deleted session '{session_id}'")
                return True
            else:
                logger.warning(f"Session '{session_id}' not found")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting session '{session_id}': {e}")
            return False

    def get_session_info(self) -> dict:
        """
        Get information about the current session state.
        
        Returns:
            Dictionary with session information
        """
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "sessions_home": str(self._sessions_home),
            "available_sessions": self.list_sessions(),
            "agent_initialized": self._agent is not None
        }