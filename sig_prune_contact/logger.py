"""Structured logging for sig-prune-contact."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


class StructuredLogger:
    """JSON and human-readable logging."""

    def __init__(self, log_file: Optional[Path] = None, verbose: bool = False):
        """Initialize logger.

        Args:
            log_file: Optional path to write JSON logs
            verbose: If True, log debug messages
        """
        self.log_file = log_file
        self.verbose = verbose
        self.logs = []

    def _write(self, level: str, message: str, data: Optional[dict] = None, is_error: bool = False):
        """Write a log entry.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Human-readable message
            data: Optional structured data
            is_error: If True, write to stderr
        """
        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
        }
        if data:
            log_entry["data"] = data

        self.logs.append(log_entry)

        # Human-readable output
        output = f"[{level}] {message}"
        if data:
            output += f" {json.dumps(data)}"

        file = sys.stderr if is_error else sys.stdout
        print(output, file=file)

        # Write JSON log if file specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

    def debug(self, message: str, data: Optional[dict] = None):
        """Log debug message."""
        if self.verbose:
            self._write("DEBUG", message, data)

    def info(self, message: str, data: Optional[dict] = None):
        """Log info message."""
        self._write("INFO", message, data)

    def warning(self, message: str, data: Optional[dict] = None):
        """Log warning message."""
        self._write("WARNING", message, data, is_error=True)

    def error(self, message: str, data: Optional[dict] = None):
        """Log error message."""
        self._write("ERROR", message, data, is_error=True)

    def get_logs(self) -> list:
        """Get all logged entries."""
        return self.logs


# Global logger instance
logger = StructuredLogger()


def set_logger_file(path: Path, verbose: bool = False):
    """Configure global logger."""
    global logger
    logger = StructuredLogger(log_file=path, verbose=verbose)
