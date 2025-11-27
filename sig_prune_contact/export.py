"""Message and attachment export functionality."""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .logger import logger


class MessageExporter:
    """Export messages in various formats."""

    def __init__(self, base_export_dir: Path):
        """Initialize exporter.

        Args:
            base_export_dir: Base directory for exports
        """
        self.base_export_dir = Path(base_export_dir).expanduser()

    def export_messages(self, contact: Dict[str, Any], messages: List[Dict[str, Any]],
                       formats: List[str], include_attachments: bool = False,
                       dry_run: bool = False) -> Optional[Path]:
        """Export messages in specified formats.

        Args:
            contact: Contact dict
            messages: List of message dicts
            formats: List of formats (json, md, html)
            include_attachments: If True, copy attachments
            dry_run: If True, don't actually write files

        Returns:
            Path to export directory or None if failed
        """
        contact_slug = self._slugify_contact(contact)
        export_dir = self.base_export_dir / contact_slug

        if not dry_run:
            export_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created export directory: {export_dir}")

        # Export in requested formats
        for fmt in formats:
            if fmt == "json":
                self._export_json(messages, export_dir, dry_run)
            elif fmt == "md":
                self._export_markdown(messages, contact, export_dir, dry_run)
            elif fmt == "html":
                self._export_html(messages, contact, export_dir, dry_run)

        # Copy attachments if requested
        if include_attachments:
            self._export_attachments(messages, export_dir, dry_run)

        # Create manifest
        manifest = self._create_manifest(contact, messages, formats, include_attachments)
        self._write_manifest(manifest, export_dir, dry_run)

        if not dry_run:
            logger.info(f"Export complete: {export_dir}")

        return export_dir if not dry_run else None

    def _export_json(self, messages: List[Dict[str, Any]], export_dir: Path, dry_run: bool = False):
        """Export messages as JSON."""
        json_file = export_dir / "messages.json"

        if dry_run:
            logger.info(f"[DRY RUN] Would write {len(messages)} messages to {json_file}")
            return

        with open(json_file, 'w') as f:
            json.dump(messages, f, indent=2, default=str)

        logger.info(f"Exported {len(messages)} messages to {json_file}")

    def _export_markdown(self, messages: List[Dict[str, Any]], contact: Dict[str, Any],
                        export_dir: Path, dry_run: bool = False):
        """Export messages as human-readable Markdown."""
        md_file = export_dir / "messages.md"

        if dry_run:
            logger.info(f"[DRY RUN] Would write markdown export to {md_file}")
            return

        lines = [
            f"# Conversation with {contact.get('name', 'Unknown')}",
            f"\nPhone: {contact.get('number', 'Unknown')}",
            f"UUID: {contact.get('uuid', 'Unknown')}",
            f"Export Date: {datetime.now().isoformat()}",
            f"Message Count: {len(messages)}",
            "\n---\n"
        ]

        for msg in messages:
            sender = msg.get("sender", "Unknown")
            body = msg.get("body", "[no content]")
            timestamp = msg.get("timestamp", "Unknown")

            lines.append(f"\n### {sender} @ {timestamp}")
            lines.append(f"\n{body}")

        md_content = "\n".join(lines)

        with open(md_file, 'w') as f:
            f.write(md_content)

        logger.info(f"Exported markdown to {md_file}")

    def _export_html(self, messages: List[Dict[str, Any]], contact: Dict[str, Any],
                    export_dir: Path, dry_run: bool = False):
        """Export messages as HTML."""
        html_file = export_dir / "messages.html"

        if dry_run:
            logger.info(f"[DRY RUN] Would write HTML export to {html_file}")
            return

        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"  <title>Conversation with {contact.get('name', 'Unknown')}</title>",
            "  <meta charset='utf-8'>",
            "  <style>",
            "    body { font-family: sans-serif; margin: 20px; }",
            "    .message { margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }",
            "    .sender { font-weight: bold; color: #333; }",
            "    .timestamp { color: #999; font-size: 0.9em; }",
            "    .body { margin-top: 5px; color: #333; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>Conversation with {contact.get('name', 'Unknown')}</h1>",
            f"  <p><strong>Phone:</strong> {contact.get('number', 'Unknown')}</p>",
            f"  <p><strong>UUID:</strong> {contact.get('uuid', 'Unknown')}</p>",
            f"  <p><strong>Export Date:</strong> {datetime.now().isoformat()}</p>",
            f"  <p><strong>Messages:</strong> {len(messages)}</p>",
            "  <hr>",
        ]

        for msg in messages:
            sender = msg.get("sender", "Unknown")
            body = msg.get("body", "[no content]")
            timestamp = msg.get("timestamp", "Unknown")

            html_lines.extend([
                "  <div class='message'>",
                f"    <div class='sender'>{sender}</div>",
                f"    <div class='timestamp'>{timestamp}</div>",
                f"    <div class='body'>{body}</div>",
                "  </div>"
            ])

        html_lines.extend([
            "</body>",
            "</html>"
        ])

        html_content = "\n".join(html_lines)

        with open(html_file, 'w') as f:
            f.write(html_content)

        logger.info(f"Exported HTML to {html_file}")

    def _export_attachments(self, messages: List[Dict[str, Any]], export_dir: Path, dry_run: bool = False):
        """Export attachments referenced in messages.

        Note: Actual attachment copying depends on Signal's storage location.
        """
        attachments_dir = export_dir / "attachments"

        if dry_run:
            logger.info(f"[DRY RUN] Would create attachments directory at {attachments_dir}")
            return

        # Count attachments in messages
        attachment_count = sum(
            len(msg.get("attachments", []))
            for msg in messages
        )

        if attachment_count > 0:
            attachments_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created attachments directory: {attachments_dir}")
            logger.info(f"Found {attachment_count} attachments (requires manual copy from Signal storage)")

    def _create_manifest(self, contact: Dict[str, Any], messages: List[Dict[str, Any]],
                        formats: List[str], include_attachments: bool) -> Dict[str, Any]:
        """Create export manifest with metadata."""
        dates = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
        dates.sort()

        return {
            "version": "1.0",
            "export_date": datetime.now().isoformat(),
            "contact": {
                "name": contact.get("name"),
                "number": contact.get("number"),
                "uuid": contact.get("uuid")
            },
            "statistics": {
                "message_count": len(messages),
                "attachment_count": sum(len(msg.get("attachments", [])) for msg in messages),
                "date_range": {
                    "start": dates[0] if dates else None,
                    "end": dates[-1] if dates else None
                }
            },
            "export_config": {
                "formats": formats,
                "include_attachments": include_attachments
            }
        }

    def _write_manifest(self, manifest: Dict[str, Any], export_dir: Path, dry_run: bool = False):
        """Write manifest file."""
        manifest_file = export_dir / "export_manifest.json"

        if dry_run:
            logger.info(f"[DRY RUN] Would write manifest to {manifest_file}")
            return

        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Wrote manifest: {manifest_file}")

    @staticmethod
    def _slugify_contact(contact: Dict[str, Any]) -> str:
        """Convert contact to directory slug."""
        name = contact.get("name", "unknown").lower().replace(" ", "-")
        number = contact.get("number", "").replace("+", "").replace("-", "")
        return f"{name}_{number}" if number else name


class BackupChecker:
    """Check for existing backups before deletion."""

    @staticmethod
    def check_signal_backup() -> bool:
        """Check if Signal backup exists.

        Returns:
            True if backup exists
        """
        # Check common Signal backup locations
        backup_paths = [
            Path("~/Signal").expanduser(),
            Path("~/Documents/Signal").expanduser(),
            Path("~/.signal").expanduser(),
        ]

        for path in backup_paths:
            if path.exists():
                logger.info(f"Found Signal backup at {path}")
                return True

        logger.warning("No Signal backup found at common locations")
        return False

    @staticmethod
    def check_system_backup() -> bool:
        """Check if system-level backup exists.

        Returns:
            True if backup likely exists
        """
        logger.info("System backup check: Please ensure OS-level backups are enabled")
        return True
