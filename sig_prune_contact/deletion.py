"""Deletion phase with confirmations and logging."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from .logger import logger


class DeletionManager:
    """Manage conversation deletion with safety checks."""

    def __init__(self, signal_cli):
        """Initialize deletion manager.

        Args:
            signal_cli: SignalCli instance
        """
        self.signal_cli = signal_cli

    def delete_conversation(self, contact: Dict[str, Any], export_dir: Path,
                           leave_groups: bool = False, dry_run: bool = False) -> bool:
        """Delete conversation for a contact.

        Args:
            contact: Contact dict
            export_dir: Path to export directory (must exist for safety)
            leave_groups: If True, also leave shared groups
            dry_run: If True, don't actually delete

        Returns:
            True if successful
        """
        # Safety check: manifest must exist
        manifest_path = export_dir / "export_manifest.json"
        if not manifest_path.exists():
            logger.error(f"Export manifest not found at {manifest_path}")
            logger.error("Refusing to delete without successful export")
            return False

        contact_id = contact.get("number") or contact.get("uuid")

        try:
            # Clear conversation history
            if not self.signal_cli.clear_conversation(contact_id, dry_run=dry_run):
                logger.error(f"Failed to clear conversation with {contact_id}")
                return False

            logger.info(f"Cleared conversation with {contact_id}")

            # Leave groups if requested
            if leave_groups:
                # This would require additional logic to identify shared groups
                pass

            # Write deletion log
            self._write_deletion_log(contact, export_dir, success=True, dry_run=dry_run)

            return True

        except Exception as e:
            logger.error(f"Error during deletion: {e}")
            self._write_deletion_log(contact, export_dir, success=False, dry_run=dry_run)
            return False

    def _write_deletion_log(self, contact: Dict[str, Any], export_dir: Path,
                           success: bool, dry_run: bool = False):
        """Write deletion log entry."""
        log_path = export_dir / "deletion_log.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "contact": contact,
            "success": success,
            "dry_run": dry_run
        }

        if dry_run:
            logger.info(f"[DRY RUN] Would write deletion log to {log_path}")
            return

        if log_path.exists():
            with open(log_path, 'r') as f:
                existing_logs = json.load(f)
        else:
            existing_logs = []

        existing_logs.append(log_entry)

        with open(log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)

        logger.info(f"Wrote deletion log: {log_path}")
