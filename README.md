# SIGSTOP - sig-prune-contact

Interactive Signal contact pruning and export tool for selectively exporting and deleting conversation histories with Signal contacts.

## Overview

`sig-prune-contact` is a command-line tool that wraps `signal-cli` to:

1. **Interactively select** a Signal contact (with fuzzy search)
2. **Export all conversation history** in multiple formats (JSON, Markdown, HTML)
3. **Optionally export attachments** with references
4. **Safely delete conversation** from your local Signal client with explicit confirmations
5. **Create audit trails** with manifests and deletion logs

## Features

### Contact Selection
- Fuzzy search by name or phone number
- Direct selection via `--contact` flag
- Preview before proceeding

### Export Formats
- **JSON**: Full raw export with timestamps, direction, body, attachment metadata
- **Markdown**: Human-readable formatted conversation
- **HTML**: Styled web-viewable archive

### Safety Features
- Export must succeed before deletion is allowed
- Requires explicit confirmation to delete (type contact name to confirm)
- `--require-backup-check` option to verify backup exists
- Structured logging to JSON for audit trails
- `--dry-run` mode to preview without side effects
- Exit codes indicate success/failure states

### Logging & Manifests
- Structured JSON logging
- `export_manifest.json` with statistics and metadata
- `deletion_log.json` recording all deletion attempts

## Installation

### Requirements
- Python 3.8+
- `signal-cli` installed and configured

### Setup
```bash
# Clone repository
git clone <repo-url>
cd SIGSTOP

# Install dependencies
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

## Usage

### Basic: Interactive Contact Selection & Export Only
```bash
sig-prune-contact
```

### Export with specific contact
```bash
sig-prune-contact --contact "+15551234567"
```

### Export with attachments in multiple formats
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --format "json,md,html" \
  --attachments
```

### Export and delete (with confirmations)
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --format "json" \
  --attachments \
  --delete \
  --require-backup-check
```

### Dry-run preview
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --dry-run
```

### Batch mode (skip confirmations)
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force
```

## CLI Reference

### Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--contact <phone\|uuid>` | Target contact (phone or UUID) | Interactive selection |
| `--export-dir <path>` | Base export directory | `~/Documents/SWORD/sigexport2/signalchats` |
| `--format <formats>` | Export formats (comma-separated: json,md,html) | `json` |
| `--attachments` | Export and copy attachments | Off |
| `--delete` | Enable deletion after successful export | Off |
| `--require-backup-check` | Verify backup exists before deletion | Off |
| `--dry-run` | Preview only, no side effects | Off |
| `--force` | Skip interactive confirmations (batch mode) | Off |
| `--leave-groups` | Also leave shared groups | Off |
| `--verbose` | Enable debug logging | Off |
| `--log-file <path>` | Write structured logs to file | None |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (export completed, optional deletion succeeded) |
| `1` | Export failed, nothing deleted |
| `2` | Export succeeded, but deletion failed |

## Workflow

### Step 1: Contact Selection
- If `--contact` provided: validate and use it
- Otherwise: show interactive fuzzy-search picker
- Display preview before proceeding

### Step 2: Fetch Messages
- Query Signal database for all messages with contact
- Count messages and show summary

### Step 3: Export Configuration
- Show export settings (format, attachments, directory)
- User confirms (unless `--force`)
- Export to specified formats

### Step 4: Export Messages
- Write `messages.json` (raw data)
- Write optional `messages.md` / `messages.html` (human-readable)
- Copy attachments if requested
- Create `export_manifest.json` with metadata

### Step 5: Deletion (if `--delete` enabled)
- Check backup if `--require-backup-check`
- Show deletion summary (message count, date range, attachments)
- Require explicit confirmation (type contact name)
- Clear conversation via `signal-cli`
- Optionally leave groups if `--leave-groups`
- Write `deletion_log.json`

## Export Structure

```
~/Documents/SWORD/sigexport2/signalchats/
├── alice-smith_15551234567/
│   ├── messages.json
│   ├── messages.md
│   ├── messages.html
│   ├── attachments/
│   │   ├── photo_001.jpg
│   │   ├── document_001.pdf
│   │   └── ...
│   ├── export_manifest.json
│   └── deletion_log.json
├── bob-jones_15559876543/
│   ├── messages.json
│   ├── export_manifest.json
│   └── ...
└── ...
```

### export_manifest.json
```json
{
  "version": "1.0",
  "export_date": "2025-11-27T10:30:00.000000",
  "contact": {
    "name": "Alice Smith",
    "number": "+15551234567",
    "uuid": "550e8400-e29b-41d4-a716-446655440000"
  },
  "statistics": {
    "message_count": 245,
    "attachment_count": 12,
    "date_range": {
      "start": "2023-01-15T14:30:00",
      "end": "2025-11-27T09:15:00"
    }
  },
  "export_config": {
    "formats": ["json", "md", "html"],
    "include_attachments": true
  }
}
```

### deletion_log.json
```json
[
  {
    "timestamp": "2025-11-27T10:35:00.000000",
    "contact": {
      "name": "Alice Smith",
      "number": "+15551234567",
      "uuid": "550e8400-e29b-41d4-a716-446655440000"
    },
    "success": true,
    "dry_run": false
  }
]
```

## Advanced Usage

### Logging to JSON
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --log-file "~/Documents/sig-prune-contact.log"
```

The log file contains structured JSON entries for automation/parsing:
```json
{"timestamp": "2025-11-27T10:30:00", "level": "INFO", "message": "Fetching contacts list..."}
{"timestamp": "2025-11-27T10:30:01", "level": "INFO", "message": "Found 42 contacts"}
...
```

### Verbose Debug Logging
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --verbose \
  --log-file "debug.log"
```

## Safety Guarantees

1. **Export-first guarantee**: No deletion happens unless `export_manifest.json` is successfully written
2. **Explicit confirmation**: Requires typing contact name to confirm deletion
3. **Backup check**: Can require backup verification before deletion
4. **Dry-run capability**: Preview all actions without side effects
5. **Audit trail**: All operations logged with timestamps
6. **Exit codes**: Clear indication of success/failure states

## Limitations & Notes

- Local deletion only (no remote deletion from other parties' devices)
- Requires `signal-cli` to be installed and configured
- Signal database location must be discoverable
- Attachment copying depends on Signal's storage structure
- Group leaving feature requires additional configuration

## Architecture

### Modules
- `signal_cli.py`: Wrapper around signal-cli commands
- `tui.py`: Terminal UI components (Rich library)
- `export.py`: Message/attachment export logic
- `deletion.py`: Deletion management with confirmations
- `logger.py`: Structured JSON logging
- `main.py`: CLI orchestration
- `utils.py`: Helper utilities

## Testing

### Unit Test (Dry-run)
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --dry-run \
  --verbose
```

### Integration Test
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --format "json,md" \
  --attachments
```

### Full Deletion Test (Force Mode)
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force \
  --require-backup-check
```

## Troubleshooting

### "signal-cli not found"
Install signal-cli:
```bash
snap install signal-cli
# or
apt install signal-cli  # (if available in your distro)
```

### "No Signal backup found"
Ensure backup exists or use `--force` to skip check:
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force
```

### "Export failed"
Check logs with verbose mode:
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --verbose \
  --dry-run
```

## Contributing

See contributing guidelines in `CONTRIBUTING.md`

## License

MIT License - See LICENSE file

## Support

For issues, features, or questions:
1. Check troubleshooting section above
2. Enable verbose logging and check logs
3. Open issue with logs attached