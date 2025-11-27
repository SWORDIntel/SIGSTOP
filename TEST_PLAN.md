# sig-prune-contact Test Plan & Execution Guide

Date: 2025-11-27
Status: Ready for Testing
Version: 0.1.0 (Prototype)

## Test Environment Setup

### Prerequisites

```bash
# 1. Install system dependencies
sudo apt-get install python3-pip python3-dev

# 2. Install signal-cli
snap install signal-cli
# or
sudo apt-get install signal-cli

# 3. Configure signal-cli
signal-cli link
# (This will register the tool with your Signal account)

# 4. Clone and setup project
cd /home/user/SIGSTOP
pip install -e .
pip install -r requirements.txt

# 5. Verify installation
which sig-prune-contact
sig-prune-contact --help
```

## Test Categories

### Category 1: Installation & Dependencies

#### Test 1.1: Package Installation
```bash
pip install -e .
which sig-prune-contact
```
**Expected**: Command available in PATH

#### Test 1.2: Dependency Check
```bash
python -c "import click, rich, fuzzywuzzy"
echo "All dependencies available"
```
**Expected**: No import errors

#### Test 1.3: Help Text
```bash
sig-prune-contact --help
```
**Expected**:
- Displays all CLI options
- Shows proper descriptions
- Usage example present

---

### Category 2: Contact Selection

#### Test 2.1: List Contacts (Help)
```bash
sig-prune-contact --help | grep -A5 "contact"
```
**Expected**: Contact option documented

#### Test 2.2: Interactive Selection (Manual)
```bash
# Run without --contact flag
sig-prune-contact
```
**Expected**:
1. Shows contact table
2. Accepts search input
3. Displays filtered contacts
4. Asks for selection
5. Shows preview
6. Asks for confirmation

#### Test 2.3: Direct Contact Argument
```bash
sig-prune-contact --contact "+15551234567" --dry-run
```
**Expected**:
- Accepts phone number format
- Proceeds without interactive selection
- Shows message "[DRY RUN]"

#### Test 2.4: UUID Contact
```bash
sig-prune-contact --contact "550e8400-e29b-41d4-a716-446655440000" --dry-run
```
**Expected**:
- Accepts UUID format
- Proceeds with dry-run

#### Test 2.5: Invalid Contact
```bash
sig-prune-contact --contact "invalid-contact" 2>&1
```
**Expected**:
- Rejects invalid format
- Shows error message
- Exit code: 1

---

### Category 3: Dry-Run Mode

#### Test 3.1: Dry-Run No Side Effects
```bash
export TEST_DIR="/tmp/sig-test-export"
mkdir -p "$TEST_DIR"

sig-prune-contact \
  --contact "+15551234567" \
  --export-dir "$TEST_DIR" \
  --dry-run \
  --format "json,md,html" \
  --attachments

# Check that nothing was created
test ! -d "$TEST_DIR/contact_*" && echo "✓ No export directory created"
```
**Expected**:
- No directories created
- No files written
- All operations prefixed with "[DRY RUN]"
- Exit code: 0

#### Test 3.2: Dry-Run With Delete Flag
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --dry-run \
  --force
```
**Expected**:
- Shows deletion summary
- Logs "[DRY RUN] Would delete..."
- No actual deletion occurs
- Exit code: 0

---

### Category 4: Export Functionality

#### Test 4.1: JSON Export
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --format "json" \
  --export-dir "/tmp/sig-export"
```
**Expected**:
- Creates directory: `/tmp/sig-export/<contact_slug>/`
- Creates file: `messages.json`
- Creates file: `export_manifest.json`
- Exit code: 0

#### Test 4.2: Multiple Formats
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --format "json,md,html" \
  --export-dir "/tmp/sig-export"

# Verify files
ls -la /tmp/sig-export/*/
```
**Expected**:
- Files created: `messages.json`, `messages.md`, `messages.html`
- `export_manifest.json` present
- All files non-empty
- HTML file is valid HTML

#### Test 4.3: Manifest Contents
```bash
cat /tmp/sig-export/*/export_manifest.json | python -m json.tool
```
**Expected JSON structure**:
```json
{
  "version": "1.0",
  "export_date": "ISO timestamp",
  "contact": {
    "name": "Contact Name",
    "number": "+1...",
    "uuid": "uuid..."
  },
  "statistics": {
    "message_count": integer,
    "attachment_count": integer,
    "date_range": {
      "start": "ISO timestamp",
      "end": "ISO timestamp"
    }
  },
  "export_config": {
    "formats": ["json", "md", "html"],
    "include_attachments": boolean
  }
}
```

#### Test 4.4: Attachments Flag
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --attachments \
  --export-dir "/tmp/sig-export"

ls -la /tmp/sig-export/*/attachments/
```
**Expected**:
- Creates `attachments/` directory
- Log indicates attachment count

#### Test 4.5: Custom Export Directory
```bash
mkdir -p ~/Custom/Export/Path
sig-prune-contact \
  --contact "+15551234567" \
  --export-dir "~/Custom/Export/Path"

ls -la ~/Custom/Export/Path/
```
**Expected**:
- Respects custom path
- Creates directory hierarchy
- Export succeeds

#### Test 4.6: Multiple Exports Same Contact
```bash
# First export
sig-prune-contact --contact "+15551234567" --export-dir "/tmp/exp1"

# Second export (should overwrite)
sig-prune-contact --contact "+15551234567" --export-dir "/tmp/exp1"

# Verify timestamps differ
cat /tmp/exp1/*/export_manifest.json | grep export_date
```
**Expected**:
- Second export overwrites first
- Manifest timestamps update

---

### Category 5: Deletion Phase

#### Test 5.1: Delete Flag Behavior
```bash
# Export-only (no delete flag)
sig-prune-contact \
  --contact "+15551234567" \
  --export-dir "/tmp/exp-only"

# Verify no deletion_log.json created
test ! -f "/tmp/exp-only/*/deletion_log.json" && echo "✓ No deletion without --delete flag"
```
**Expected**:
- No `deletion_log.json` created
- Conversation not deleted
- Exit code: 0

#### Test 5.2: Delete Without Backup Check
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force \
  --export-dir "/tmp/exp-delete"
```
**Expected**:
- Export succeeds
- Deletion confirmation skipped (--force)
- `deletion_log.json` created
- Exit code: 0 (if deletion succeeds) or 2 (if fails)

#### Test 5.3: Deletion Log Format
```bash
cat /tmp/exp-delete/*/deletion_log.json | python -m json.tool
```
**Expected JSON structure**:
```json
[
  {
    "timestamp": "ISO timestamp",
    "contact": {
      "name": "...",
      "number": "...",
      "uuid": "..."
    },
    "success": boolean,
    "dry_run": false
  }
]
```

#### Test 5.4: Require Backup Check
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --require-backup-check \
  --force
```
**Expected**:
- Checks for backup before deletion
- Proceeds if backup found
- Skipped with --force

---

### Category 6: CLI Flags

#### Test 6.1: Verbose Logging
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --verbose \
  --dry-run
```
**Expected**:
- DEBUG level messages appear
- More detailed output

#### Test 6.2: Log File Output
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --log-file "/tmp/test.log"

cat /tmp/test.log | head -5
```
**Expected**:
- Each line is valid JSON
- Contains timestamp, level, message
- Valid JSON structure: `jq < /tmp/test.log`

#### Test 6.3: Force Flag
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force \
  --dry-run 2>&1 | grep -i "confirmation"
```
**Expected**:
- No confirmation prompts
- Proceeds directly to execution

#### Test 6.4: Leave Groups
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --leave-groups \
  --dry-run
```
**Expected**:
- Logs group operations (in dry-run)
- Command accepts flag

---

### Category 7: Exit Codes

#### Test 7.1: Success (Export Only)
```bash
sig-prune-contact --contact "+15551234567" --format "json"
echo "Exit code: $?"
```
**Expected**: Exit code 0

#### Test 7.2: Success (Export + Delete)
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force \
  --dry-run

echo "Exit code: $?"
```
**Expected**: Exit code 0 (dry-run success) or actual behavior

#### Test 7.3: Export Failed
```bash
sig-prune-contact --contact "totally-invalid-contact"
echo "Exit code: $?"
```
**Expected**: Exit code 1

#### Test 7.4: Delete Failed
```bash
# This requires actual failure conditions
# May need mocking or special setup
sig-prune-contact \
  --contact "+15551234567" \
  --delete \
  --force

echo "Exit code: $?"
```
**Expected**: Exit code 2 if deletion fails, 0 if succeeds

---

### Category 8: Error Handling

#### Test 8.1: signal-cli Not Found
```bash
# Temporarily make signal-cli unavailable
PATH=/tmp/empty:$PATH sig-prune-contact --contact "+15551234567" 2>&1
```
**Expected**:
- Error message about signal-cli
- Exit code: 1

#### Test 8.2: Invalid Export Directory
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --export-dir "/root/no-permission"
```
**Expected**:
- Appropriate error message
- Exit code: 1

#### Test 8.3: Interrupted Operation
```bash
sig-prune-contact --contact "+15551234567" &
PID=$!
sleep 1
kill -INT $PID
wait $PID 2>/dev/null
echo "Exit code: $?"
```
**Expected**:
- Handles Ctrl+C gracefully
- Exit code: 1 (interrupted)

---

### Category 9: Data Validation

#### Test 9.1: Format Validation
```bash
sig-prune-contact \
  --contact "+15551234567" \
  --format "invalid-format" 2>&1
```
**Expected**:
- Rejects invalid format
- Shows valid options
- Exit code: 1

#### Test 9.2: Path Expansion
```bash
sig-prune_contact \
  --contact "+15551234567" \
  --export-dir "~/test/export"

test -d ~/test/export && echo "✓ Path expansion works"
```
**Expected**:
- Expands `~` to home directory
- Creates nested directories

#### Test 9.3: Contact Argument Validation
```bash
# Valid phone
sig-prune-contact --contact "+15551234567" --dry-run

# Valid UUID
sig-prune-contact --contact "550e8400-e29b-41d4-a716-446655440000" --dry-run

# Invalid
sig-prune-contact --contact "not-valid" 2>&1
```
**Expected**:
- Accepts valid formats
- Rejects invalid formats

---

### Category 10: Integration Tests

#### Test 10.1: Full Workflow (Dry-Run)
```bash
# Complete workflow without side effects
sig-prune-contact \
  --contact "+15551234567" \
  --format "json,md,html" \
  --attachments \
  --delete \
  --require-backup-check \
  --log-file "/tmp/full-test.log" \
  --verbose \
  --dry-run

echo "Exit code: $?"
```
**Expected**:
- All phases execute
- No files created
- Exit code: 0
- Logs written to file

#### Test 10.2: Full Workflow (Real)
```bash
# Actual export and delete
sig-prune-contact \
  --contact "+15551234567" \
  --format "json" \
  --delete \
  --force \
  --require-backup-check \
  --export-dir "/tmp/full-export"

# Verify results
ls -la /tmp/full-export/*/
cat /tmp/full-export/*/deletion_log.json | python -m json.tool
```
**Expected**:
- Export directory created
- Manifest and logs present
- Conversation deleted (if command available)

---

## Test Execution Report Template

```markdown
# Test Execution Report
Date: YYYY-MM-DD
Tester: <Name>
Version: 0.1.0

## Test Summary
- Total Tests: XX
- Passed: XX
- Failed: XX
- Blocked: XX
- Skipped: XX

## Results by Category

### Category 1: Installation & Dependencies
- Test 1.1: PASS/FAIL/BLOCKED
- Test 1.2: PASS/FAIL/BLOCKED
- Test 1.3: PASS/FAIL/BLOCKED

### Category 2: Contact Selection
...

## Failed Tests Details
- Test 2.5: Invalid Contact
  - Expected: ...
  - Actual: ...
  - Root Cause: ...
  - Resolution: ...

## Recommendations
- ...

## Sign-off
Tester: _________________ Date: ________
Reviewer: _______________ Date: ________
```

---

## Quick Test Script

```bash
#!/bin/bash
# quick-test.sh - Run all basic tests

set -e

echo "=== sig-prune-contact Quick Test Suite ==="

# 1. Installation
echo -e "\n[1/5] Testing installation..."
pip install -e . > /dev/null 2>&1
which sig-prune-contact

# 2. Help
echo "[2/5] Testing help..."
sig-prune-contact --help | head -10

# 3. Dry-run
echo "[3/5] Testing dry-run..."
sig-prune-contact --contact "+15551234567" --dry-run --format "json" 2>&1 | grep "DRY RUN" || true

# 4. Syntax check
echo "[4/5] Checking Python syntax..."
python -m py_compile sig_prune_contact/*.py

# 5. Imports
echo "[5/5] Testing imports..."
python -c "from sig_prune_contact import __version__; print(f'Version: {__version__}')"

echo -e "\n✓ Quick test suite completed"
```

---

## Performance Testing

### Large Conversation Export
```bash
# Export a conversation with 5000+ messages
time sig-prune-contact \
  --contact "+15551234567" \
  --format "json,md" \
  --export-dir "/tmp/large-export"

# Monitor memory usage
python -m memory_profiler sig_prune_contact/main.py
```

**Expected**:
- Completes in <60 seconds
- Memory usage <500MB
- All messages exported

---

## Platform Testing

Test on multiple platforms:
- [ ] Linux (Ubuntu 20.04+)
- [ ] Linux (Fedora 35+)
- [ ] macOS (Monterey+)
- [ ] Windows WSL2

## Python Version Testing

Test with multiple Python versions:
- [ ] Python 3.8
- [ ] Python 3.9
- [ ] Python 3.10
- [ ] Python 3.11

---

## Sign-off Criteria

The tool is ready for production use when:

- [ ] All Category 1-5 tests pass (Installation, Contact Selection, Dry-Run, Export, Deletion)
- [ ] All CLI flags work correctly (Category 6)
- [ ] Exit codes are correct (Category 7)
- [ ] Error handling is appropriate (Category 8)
- [ ] Data validation works (Category 9)
- [ ] Integration test passes (Category 10)
- [ ] No critical security issues found
- [ ] Performance acceptable for typical use
- [ ] Works on at least 2 platforms
- [ ] Works on at least 2 Python versions

---

## Regression Testing

After any code changes:

```bash
# Quick smoke test
./quick-test.sh

# Full test suite
pytest tests/ -v

# Coverage report
pytest tests/ --cov=sig_prune_contact
```

---

## Notes

- Tests assume signal-cli is properly configured
- Some tests require actual Signal conversations to exist
- Deletion tests are destructive and should use test contacts
- Performance tests may require Signal app running
