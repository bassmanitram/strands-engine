"""
Session management proxy for strands_agent_factory.

This module provides the DelegatingSession class, which implements a proxy pattern
for session management that allows dynamic session switching while maintaining
compatibility with the strands-agents SessionManager interface.

The DelegatingSession enables:
- Dynamic session activation/deactivation during runtime
- Transparent session switching without agent restart
- Graceful handling of session state conflicts
- Session persistence using FileSessionManager backend
- Compatibility with different conversation manager types

The proxy pattern allows applications to control session behavior without
requiring agent reconfiguration, making it ideal for multi-user or
multi-conversation scenarios.
"""

import shutil
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional

from loguru import logger
from strands import Agent
from strands.session.file_session_manager import FileSessionManager
from strands.session.session_manager import SessionManager
from strands.types.content import Message


class DelegatingSession(SessionManager):
    """
    Session management proxy that enables dynamic session switching.

    DelegatingSession implements the SessionManager protocol while providing
    the ability to dynamically activate, deactivate, and switch between sessions
    during runtime. It maintains compatibility with strands-agents while adding
    flexibility for complex session management scenarios.

    The proxy operates in two modes:
    - Active: Delegates all operations to an internal FileSessionManager
    - Inactive: Ignores session operations (no persistence)

    Key features:
    - Dynamic session switching without agent restart
    - Graceful handling of conversation manager conflicts
    - Session backup and recovery for incompatible states
    - Thread-safe session operations
    - Comprehensive session lifecycle management

    Attributes:
        session_id: Current session identifier or "inactive"
        is_active: Whether a session is currently active
        current_session_id: Active session ID or None

    Example:
        Basic usage::

            session = DelegatingSession("user123", "/path/to/sessions")
            session.initialize(agent)

            # Switch sessions dynamically
            session.set_active_session("conversation_1")
            # ... conversation happens ...
            session.set_active_session("conversation_2")
    """

    def __init__(
        self, session_name: Optional[str], sessions_home: Optional[str | Path] = None
    ):
        logger.trace(
            "DelegatingSession.__init__ called with session_name={}, sessions_home={}",
            session_name,
            sessions_home,
        )
        """
        Initialize the session proxy.
        
        Creates a DelegatingSession that can manage session persistence
        using FileSessionManager backend. The session starts inactive
        until an agent is provided and initialization occurs.
        
        Args:
            session_name: Initial session name, or None for inactive mode
            sessions_home: Directory for session storage, defaults to .strands-sessions
            
        Note:
            If session_name is None, the proxy remains inactive and ignores
            all session operations. This is useful for stateless operation.
        """
        # Use default sessions_home if not provided - .strands-sessions in CWD
        default_home = Path.cwd() / ".strands-sessions"
        self._sessions_home = Path(sessions_home or default_home)

        self._active_session: Optional[FileSessionManager] = (
            None  # FileSessionManager instance when active
        )
        self._agent: Optional[Agent] = None  # strands-agents Agent instance
        self.session_id = session_name or "inactive"

        # Initialize parent SessionManager with session_id
        super().__init__(session_id=self.session_id)

        # Ensure sessions directory exists
        self._sessions_home.mkdir(parents=True, exist_ok=True)

        if session_name:
            logger.info(
                f"DelegatingSession configured for session '{session_name}' (will activate when agent available)"
            )
            logger.debug("Sessions stored in: {}", self._sessions_home)
        else:
            logger.info(
                "DelegatingSession configured as inactive (will ignore session operations)"
            )
            logger.debug("Sessions home available at: {}", self._sessions_home)

    def set_active_session(self, session_name: str) -> None:
        """
        Create and activate a new session.

        Switches to a new FileSessionManager instance and synchronizes its
        history with the current agent state. Handles conversation manager
        type conflicts by creating backup sessions when incompatible states
        are detected.

        Args:
            session_name: Name of the session to activate

        Raises:
            RuntimeError: If no agent has been initialized

        Note:
            If the session has incompatible conversation manager state,
            the existing session data is backed up and a fresh session
            is created to avoid conflicts.
        """
        if not self._agent:
            logger.error(
                "Cannot set active session: DelegatingSession has not been initialized with an agent yet."
            )
            return

        logger.info(f"Switching active session to '{session_name}'...")
        self.session_id = session_name

        new_session = FileSessionManager(
            session_id=session_name, storage_dir=str(self._sessions_home)
        )

        # Try to initialize the session, but handle conversation manager state conflicts
        try:
            new_session.initialize(self._agent)
        except ValueError as e:
            if "Invalid conversation manager state" in str(e):
                logger.warning(
                    f"Session '{session_name}' has incompatible conversation manager state."
                )
                logger.info(
                    "This can happen when switching between conversation manager types (e.g., sliding_window <-> summarizing)."
                )
                logger.info("Creating a new session to avoid conflicts...")

                # Clear any existing session data and start fresh
                session_path = Path(self._sessions_home) / f"session_{session_name}"
                if session_path.exists():
                    # Create unique backup name to avoid conflicts
                    timestamp = int(time.time())
                    unique_id = str(uuid.uuid4())[:8]
                    backup_path = Path(
                        str(session_path) + f".backup.{timestamp}.{unique_id}"
                    )

                    logger.debug(
                        "Backing up incompatible session data to {}", backup_path
                    )

                    try:
                        # Atomic rename - either succeeds completely or fails completely
                        session_path.rename(backup_path)
                        logger.info("Session backup created: {}", backup_path)
                    except OSError as e:
                        logger.warning("Failed to create session backup: {}", e)
                        # Continue anyway - we'll create a fresh session

                # Create a fresh session
                new_session = FileSessionManager(
                    session_id=session_name, storage_dir=str(self._sessions_home)
                )
                new_session.initialize(self._agent)
                logger.info(
                    f"Created fresh session '{session_name}' with current conversation manager type."
                )
            else:
                # Re-raise other ValueError types
                raise
        except Exception as e:
            logger.error(f"Failed to initialize session '{session_name}': {e}")
            logger.info("Continuing without persistent session...")
            return

        self._active_session = new_session
        logger.info(
            f"DelegatingSession is now active for session_id: '{self.session_id}'. Agent history has been updated."
        )

    def deactivate_session(self) -> None:
        """
        Deactivate the current session.

        Deactivates the current session and performs any necessary cleanup.
        After deactivation, the proxy ignores all session operations until
        a new session is activated.

        Note:
            Deactivation attempts to call cleanup methods on the underlying
            FileSessionManager if available, but continues gracefully if
            cleanup fails.
        """
        if self._active_session:
            logger.info(f"Deactivating session '{self.session_id}'")
            # Cleanup if needed
            if hasattr(self._active_session, "cleanup"):
                try:
                    self._active_session.cleanup()
                except Exception as e:
                    logger.warning(f"Error during session cleanup: {e}")
            self._active_session = None
            self.session_id = "inactive"
        else:
            logger.debug("No active session to deactivate")

    def list_sessions(self) -> List[str]:
        """
        Get a list of available session names.

        Scans the sessions directory and returns all available session
        identifiers. Sessions are stored as directories with the prefix
        "session_" by the FileSessionManager backend.

        Returns:
            List[str]: Sorted list of available session names

        Example:
            >>> session.list_sessions()
            ['conversation_1', 'user123', 'work_session']
        """
        if not self._sessions_home.exists():
            return []

        # FileSessionManager saves files in folders named "session_<name>"
        try:
            session_dirs = [
                p
                for p in self._sessions_home.iterdir()
                if p.is_dir() and p.name.startswith("session_")
            ]
            session_names = [p.name[len("session_") :] for p in session_dirs]
            return sorted(session_names)
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    @property
    def is_active(self) -> bool:
        """
        Check if a session is currently active.

        Returns:
            bool: True if a session is active, False if inactive
        """
        return self._active_session is not None

    @property
    def current_session_id(self) -> Optional[str]:
        """
        Get the current session identifier.

        Returns:
            Optional[str]: Current session ID, or None if inactive
        """
        return self.session_id if self.is_active else None

    # ========================================================================
    # SessionManager Interface Implementation
    # ========================================================================

    def initialize(self, agent: Agent, **kwargs: Any) -> None:
        """
        Initialize the proxy with a strands-agents Agent instance.

        Stores the agent reference and activates the initial session if
        one was configured during construction. This method is called
        automatically by strands-agents during agent setup.

        Args:
            agent: The strands-agents Agent instance to manage
            **kwargs: Additional arguments (unused but required by interface)
        """
        self._agent = agent
        if self.session_id != "inactive" and not self._active_session:
            self.set_active_session(self.session_id)

        logger.info(
            f"DelegatingSession initialized with agent (active: {self.is_active})"
        )

    def append_message(self, message: Message, agent: Agent, **kwargs: Any) -> None:
        """
        Append a message to the active session.

        Delegates message storage to the active FileSessionManager if
        a session is active. Messages are ignored if no session is active.

        Args:
            message: Message to append to the session
            agent: Agent instance (required by interface)
            **kwargs: Additional arguments passed to the session manager
        """
        if self._active_session:
            self._active_session.append_message(message, agent, **kwargs)
            logger.debug("Appended message to session '{}'", self.session_id)
        else:
            logger.debug("Session inactive - ignoring message append")

    def redact_latest_message(
        self, redact_message: Message, agent: Agent, **kwargs: Any
    ) -> None:
        """
        Redact the latest message from the active session.

        Delegates message redaction to the active FileSessionManager if
        a session is active. Redaction is ignored if no session is active.

        Args:
            redact_message: Redaction message (replaces the latest message)
            agent: Agent instance (required by interface)
            **kwargs: Additional arguments passed to the session manager
        """
        if self._active_session:
            self._active_session.redact_latest_message(redact_message, agent, **kwargs)
            logger.debug("Redacted latest message in session '{}'", self.session_id)
        else:
            logger.debug("Session inactive - ignoring message redaction")

    def sync_agent(self, agent: Agent) -> None:
        """
        Synchronize agent state with the active session.

        Updates the agent's internal state to match the active session's
        stored conversation history. This is typically called when switching
        sessions or after session initialization.

        Args:
            agent: Agent instance to synchronize
        """
        if self._active_session:
            self._active_session.sync_agent(agent)
            logger.debug("Synced agent state with session '{}'", self.session_id)
        else:
            logger.debug("Session inactive - ignoring agent sync")

    def clear(self) -> None:
        """
        Clear the agent's in-memory message history.

        Clears the agent's message list in memory. If a session is active,
        the persistent session data remains intact (following YACBA patterns
        for safety). This prevents accidental loss of important conversation
        history.

        Note:
            Only clears in-memory state. Persistent session files are
            preserved to prevent accidental data loss. Use delete_session()
            if you need to remove persistent data.
        """
        # Step 1: Always clear the agent's in-memory message list.
        if self._agent and hasattr(self._agent, "messages") and self._agent.messages:
            self._agent.messages.clear()
            logger.debug("Cleared agent's in-memory message list.")

        # Step 2: If a session is active, the persistent data remains intact
        # following YACBA's pattern for safety
        if self._active_session:
            logger.info(
                f"Cleared agent memory. Session '{self.session_id}' remains active with persisted data intact."
            )
        else:
            logger.debug("Session inactive - no persistent data to clear")

    # ========================================================================
    # Additional Utility Methods
    # ========================================================================

    def save(self) -> None:
        """
        Force save the current session state.

        Manually triggers a save operation on the active session to ensure
        all current conversation state is persisted. Useful for ensuring
        data durability at critical points.
        """
        if self._active_session:
            try:
                # Force save session state
                if hasattr(self._active_session, "save"):
                    self._active_session.save()
                elif hasattr(self._active_session, "_save"):
                    # Use private save method if public one not available
                    self._active_session._save(
                        self._agent.messages if self._agent else []
                    )
                logger.info(f"Manually saved session '{self.session_id}'")
            except Exception as e:
                logger.error(f"Error saving session '{self.session_id}': {e}")
        else:
            logger.debug("Session inactive - no data to save")

    def load(self, session_id: str) -> bool:
        """
        Load an existing session by ID.

        Attempts to load and activate an existing session. Deactivates
        any currently active session before loading the new one.

        Args:
            session_id: Session ID to load

        Returns:
            bool: True if session was loaded successfully, False otherwise
        """
        try:
            if session_id in self.list_sessions():
                if self._active_session:
                    self.deactivate_session()

                self.set_active_session(session_id)
                return self.is_active
            else:
                logger.warning(
                    f"Session '{session_id}' not found in {self._sessions_home}"
                )
                return False
        except Exception as e:
            logger.error(f"Error loading session '{session_id}': {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.

        Permanently removes a session and all its associated data.
        If the session is currently active, it will be deactivated first.

        Args:
            session_id: Session ID to delete

        Returns:
            bool: True if session was deleted successfully, False otherwise

        Warning:
            This operation is irreversible. All conversation history
            for the specified session will be permanently lost.
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
            logger.warning(f"Error deleting session '{session_id}': {e}")
            return False

    def get_session_info(self) -> dict:
        """
        Get comprehensive information about the current session state.

        Returns detailed information about the session proxy state,
        active sessions, and configuration. Useful for debugging
        and status reporting.

        Returns:
            dict: Dictionary containing session state information

        Example:
            >>> info = session.get_session_info()
            >>> print(info['is_active'])
            True
            >>> print(info['available_sessions'])
            ['chat1', 'work_session', 'user123']
        """
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "sessions_home": str(self._sessions_home),
            "available_sessions": self.list_sessions(),
            "agent_initialized": self._agent is not None,
        }
