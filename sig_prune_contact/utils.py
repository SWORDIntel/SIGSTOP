"""Utility functions."""

from pathlib import Path
from typing import List, Optional
import re


def parse_contact_argument(contact_arg: str) -> Optional[dict]:
    """Parse contact from command-line argument.

    Args:
        contact_arg: Phone number (e.g., +15551234567) or UUID

    Returns:
        Dict with number or uuid key, or None if invalid
    """
    if not contact_arg:
        return None

    # Check if it looks like a phone number
    if contact_arg.startswith('+') or contact_arg[0].isdigit():
        return {"number": contact_arg}

    # Check if it looks like a UUID
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if re.match(uuid_pattern, contact_arg.lower()):
        return {"uuid": contact_arg}

    return None


def expand_export_path(export_dir: str) -> Path:
    """Expand and validate export directory path.

    Args:
        export_dir: Path string (may contain ~)

    Returns:
        Expanded Path object
    """
    path = Path(export_dir).expanduser()
    return path


def validate_formats(formats_str: str) -> List[str]:
    """Validate and parse format string.

    Args:
        formats_str: Comma-separated formats (json,md,html)

    Returns:
        List of validated formats

    Raises:
        ValueError: If invalid format
    """
    valid_formats = {"json", "md", "html"}
    formats = [f.strip().lower() for f in formats_str.split(",")]

    for fmt in formats:
        if fmt not in valid_formats:
            raise ValueError(f"Invalid format: {fmt}. Must be one of: {valid_formats}")

    return formats


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
