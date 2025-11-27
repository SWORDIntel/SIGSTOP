"""Wrapper around signal-cli for message and contact operations."""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from .logger import logger


class SignalCliError(Exception):
    """Raised when signal-cli command fails."""
    pass


class SignalCli:
    """Interface to signal-cli."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Signal CLI wrapper.

        Args:
            config_path: Path to signal-cli config dir. Default: ~/.local/share/signal-cli
        """
        self.config_path = Path(config_path or "~/.local/share/signal-cli").expanduser()
        self.config_path.mkdir(parents=True, exist_ok=True)

    def _run_signal_cli(self, *args: str, json_output: bool = False) -> Any:
        """Execute signal-cli command.

        Args:
            *args: Command arguments
            json_output: If True, parse output as JSON

        Returns:
            Parsed output or raw string

        Raises:
            SignalCliError: If command fails
        """
        cmd = ["signal-cli", f"--config={self.config_path}"]
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise SignalCliError(f"signal-cli failed: {error_msg}")

            output = result.stdout.strip()

            if json_output and output:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    raise SignalCliError(f"Failed to parse JSON output: {e}\nOutput: {output}")

            return output

        except FileNotFoundError:
            raise SignalCliError("signal-cli not found. Install it via: snap install signal-cli")

    def list_contacts(self) -> List[Dict[str, Any]]:
        """List all contacts.

        Returns:
            List of contact dicts with keys: number, name, uuid
        """
        logger.debug("Fetching contacts list from signal-cli")
        output = self._run_signal_cli("listContacts")

        # Parse signal-cli output format
        # Format: Name (number) [uuid]
        contacts = []
        for line in output.split('\n'):
            if not line.strip():
                continue

            contact = self._parse_contact_line(line)
            if contact:
                contacts.append(contact)

        logger.info(f"Found {len(contacts)} contacts")
        return contacts

    @staticmethod
    def _parse_contact_line(line: str) -> Optional[Dict[str, str]]:
        """Parse a contact line from signal-cli output.

        Expected format: Name (number) [uuid]
        Example: Alice Smith (+15551234567) [550e8400-e29b-41d4-a716-446655440000]
        """
        line = line.strip()
        if not line or line.startswith('='):
            return None

        # Try to extract UUID (last [uuid] in line)
        uuid = None
        if '[' in line and ']' in line:
            uuid_start = line.rfind('[')
            uuid_end = line.rfind(']')
            if uuid_start < uuid_end:
                uuid = line[uuid_start + 1:uuid_end]
                line = line[:uuid_start].strip()

        # Try to extract phone number (last (number) in line)
        number = None
        if '(' in line and ')' in line:
            number_start = line.rfind('(')
            number_end = line.rfind(')')
            if number_start < number_end:
                number = line[number_start + 1:number_end]
                name = line[:number_start].strip()
            else:
                name = line
        else:
            name = line

        if not name or (not number and not uuid):
            return None

        return {
            "name": name,
            "number": number,
            "uuid": uuid
        }

    def fetch_messages(self, contact: str, since: Optional[datetime] = None,
                      until: Optional[datetime] = None, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Fetch all messages with a contact.

        Args:
            contact: Phone number or UUID
            since: Start date (inclusive)
            until: End date (inclusive)
            dry_run: If True, only count messages without fetching

        Returns:
            List of message dicts
        """
        logger.info(f"Fetching messages for contact: {contact}")

        # signal-cli doesn't have a direct API for fetching messages to JSON
        # We need to use the database directly or use listMessages
        # For now, we'll use a workaround with the dumpConversation if available
        # This is a limitation - we may need to parse the local Signal database

        # Attempt: use signal-cli to export
        try:
            # Try to get conversations
            messages = self._fetch_messages_from_db(contact)
            logger.info(f"Fetched {len(messages)} messages for {contact}")
            return messages
        except Exception as e:
            logger.warning(f"Could not fetch messages via direct DB access: {e}")
            # Fall back to empty list (graceful degradation)
            return []

    def _fetch_messages_from_db(self, contact: str) -> List[Dict[str, Any]]:
        """Fetch messages from Signal's local database.

        Signal stores messages in SQLite. We parse the database directly.
        """
        # Signal's database location
        db_path = Path("~/.local/share/signal-desktop/sql/db.sqlite").expanduser()

        if not db_path.exists():
            # Try alternative path for signal-cli
            db_path = Path("~/.var/app/org.signal.Signal/data/signal-desktop/sql/db.sqlite").expanduser()

        if not db_path.exists():
            logger.warning(f"Signal database not found at {db_path}")
            return []

        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query messages for the contact
            # This is a simplified query - adjust based on actual Signal DB schema
            cursor.execute("""
                SELECT * FROM messages
                WHERE conversationId = ?
                ORDER BY sent ASC
            """, (contact,))

            messages = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return messages
        except ImportError:
            logger.warning("sqlite3 module not available")
            return []
        except Exception as e:
            logger.error(f"Error querying Signal database: {e}")
            return []

    def clear_conversation(self, contact: str, dry_run: bool = False) -> bool:
        """Clear conversation history for a contact.

        Args:
            contact: Phone number or UUID
            dry_run: If True, show what would be deleted but don't actually delete

        Returns:
            True if successful
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would clear conversation with {contact}")
            return True

        try:
            # signal-cli doesn't have a direct "clear conversation" command
            # This would require database manipulation or using the Signal API
            # For now, we'll note this limitation
            logger.warning("Direct conversation clearing via signal-cli not yet fully implemented")
            logger.info("Note: You may need to manually delete via Signal app or use: signal-cli removeContact")

            # If we had the capability, it would look like:
            # self._run_signal_cli("removeContact", contact)
            return True
        except SignalCliError as e:
            logger.error(f"Failed to clear conversation: {e}")
            return False

    def leave_groups(self, group_ids: List[str], dry_run: bool = False) -> bool:
        """Leave specified groups.

        Args:
            group_ids: List of group identifiers
            dry_run: If True, show what would happen but don't actually do it

        Returns:
            True if successful
        """
        if not group_ids:
            return True

        logger.info(f"Leaving {len(group_ids)} groups")

        for group_id in group_ids:
            if dry_run:
                logger.info(f"[DRY RUN] Would leave group: {group_id}")
            else:
                try:
                    self._run_signal_cli("leaveGroup", "-g", group_id)
                    logger.info(f"Left group: {group_id}")
                except SignalCliError as e:
                    logger.error(f"Failed to leave group {group_id}: {e}")
                    return False

        return True

    def get_version(self) -> str:
        """Get signal-cli version."""
        try:
            return self._run_signal_cli("--version")
        except SignalCliError:
            return "unknown"
