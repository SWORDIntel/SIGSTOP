# sig-prune-contact TUI Design Guide

**Version**: 0.1.0
**Date**: 2025-11-27
**Focus**: Terminal User Interface (TUI) Enhancement

---

## Overview

The `sig-prune-contact` tool features a rich, interactive Terminal User Interface (TUI) built with the **Rich** library. The TUI provides visual feedback, progress indicators, and professional formatting to guide users through the contact pruning workflow.

---

## Visual Components

### 1. Contact Selection Interface

#### Contact Table Display
Shows all available Signal contacts in a formatted table:

```
╭──────────────────────────────────────────────────────────────╮
│ Signal Contacts                                              │
├────┬──────────────────┬──────────────────┬──────────────────┤
│ #  │ Name             │ Number           │ UUID             │
├────┼──────────────────┼──────────────────┼──────────────────┤
│ 1  │ Alice Smith      │ +15551234567     │ 550e8400...0000  │
│ 2  │ Bob Jones        │ +15559876543     │ 6ba7b810...8681  │
│ 3  │ Carol White      │ +15552468135     │ 6ba7b811...0001  │
╰────┴──────────────────┴──────────────────┴──────────────────╯
```

**Features**:
- Column-by-column highlighting with different colors
- UUID truncated to first 8 + last 8 characters for readability
- Numbered rows for easy selection

#### Fuzzy Search Filtering
```
Search contacts (name or number, or leave blank to see all): ali

╭──────────────────────────────────────────────────────────────╮
│ Signal Contacts                                              │
├────┬──────────────────┬──────────────────┬──────────────────┤
│ #  │ Name             │ Number           │ UUID             │
├────┼──────────────────┼──────────────────┼──────────────────┤
│ 1  │ Alice Smith      │ +15551234567     │ 550e8400...0000  │
╰────┴──────────────────┴──────────────────┴──────────────────╯

Filtered: 1 contacts
```

**Features**:
- Real-time fuzzy matching (60% cutoff for quality results)
- Shows filtered count
- Matches on both name and phone number

#### Contact Preview
```
╭─────────────────────────────────────────────────────────────╮
│ Contact Preview                                             │
├─────────────────────────────────────────────────────────────┤
│ Name:   Alice Smith                                         │
│ Number: +15551234567                                        │
│ UUID:   550e8400-e29b-41d4-a716-446655440000               │
╰─────────────────────────────────────────────────────────────╯

Proceed with this contact? [y/N]:
```

**Features**:
- Clean panel layout with selected contact details
- UUID displayed in full
- Confirmation before proceeding

---

### 2. Operation Progress Indicators

#### Spinner for Long Operations
```
⠼ Fetching messages from Signal database...
```

Displays while:
- Listing contacts from signal-cli
- Querying message database
- Checking authentication status
- Initializing operations

**Features**:
- Animated spinner (⠙, ⠹, ⠸, ⠼, ⠴, ⠦, ⠧, ⠇, ⠏)
- Real-time status updates
- Non-blocking terminal interaction

#### Progress Bar with Speed
```
Exporting messages... ▏████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ 234 B / 1.2 KB (45.3 KiB/s)
```

Displays during:
- Message export to multiple formats
- Attachment processing
- Batch operations

**Features**:
- Visual progress bar (0-100%)
- Current / Total indicators
- Real-time transfer speed (msg/s, KB/s)
- Animated spinner
- Percentage completion

#### Step Completion Indicators
```
✓ Contact selected: Alice Smith (+15551234567)
✓ Found 245 messages
✓ Confirmed export configuration
✓ Exported to JSON format
✓ Exported to Markdown format
✓ Export manifest created
```

**Features**:
- Green checkmark (✓) for success
- Red X (✗) for failure
- Clear step descriptions
- Sequential display

---

### 3. Confirmation Dialogs

#### Export Configuration Panel
```
╭────────────────────────────────────────────────────────────╮
│ Export Configuration                                       │
├────────────────────────────────────────────────────────────┤
│ Contact:          Alice Smith (+15551234567)              │
│ Export Directory: ~/Documents/SWORD/sigexport2/signalchats │
│ Formats:          json, md, html                           │
│ Attachments:      Yes                                      │
│ Messages to Export: 245                                    │
│ Mode:             LIVE                                     │
╰────────────────────────────────────────────────────────────╯

Proceed with export? [y/N]:
```

**Features**:
- Organized key-value display
- Clear mode indicator (LIVE vs DRY RUN)
- Attachment status
- Confirmable before proceeding

#### Deletion Warning Panel
```
╭────────────────────────────────────────────────────────────╮
│ ⚠️  DELETION SUMMARY                                        │
├────────────────────────────────────────────────────────────┤
│ Messages:       245                                         │
│ Attachments:    12                                          │
│ Date Range:     2023-01-15 to 2025-11-27                  │
│ Contact:        Alice Smith (+15551234567)                 │
│ Mode:           LIVE DELETION                               │
╰────────────────────────────────────────────────────────────╯

Type the contact name to confirm deletion: alice-smith
Confirmation:
```

**Features**:
- Red warning styling for destructive operation
- Full deletion summary
- Warning icon (⚠️)
- Requires explicit confirmation (type contact name)
- Contact slug displayed for typing

---

### 4. Authentication Status

#### Authentication Check Success
```
Checking Signal authentication status...

╭────────────────────────────────────────────────────────────╮
│ Authentication Check                                       │
├────────────────────────────────────────────────────────────┤
│ ✓ Authentication Status: OK                                │
│ signal-cli version: 0.15.0                                 │
│ Authenticated: True                                        │
│ Config path: /home/user/.local/share/signal-cli            │
╰────────────────────────────────────────────────────────────╯
```

#### Authentication Check Failure
```
Checking Signal authentication status...

╭────────────────────────────────────────────────────────────╮
│ Authentication Required                                    │
├────────────────────────────────────────────────────────────┤
│ ✗ Not authenticated                                        │
│ Please run: signal-cli link                                │
│ Or ensure signal-cli is properly configured.              │
╰────────────────────────────────────────────────────────────╯
```

**Features**:
- Green panel for success
- Red panel for failure
- Actionable error messages
- Config path provided

---

### 5. Export Summary

#### Export Completion Summary
```
╭────────────────────────────────────────────────────────────╮
│ ✓ Export Summary                                            │
├────────────────────────────────────────────────────────────┤
│ Contact:    Alice Smith (+15551234567)                    │
│ Messages:   245                                            │
│ Attachments: 12                                            │
│ Date Range: 2023-01-15 to 2025-11-27                      │
│ Formats:    json, md, html                                 │
│ Export Date: 2025-11-27T10:30:00.000000                   │
╰────────────────────────────────────────────────────────────╯
```

**Features**:
- Green border for success
- Contact and message details
- All export formats listed
- Timestamp of export

#### Operation Summary with Statistics
```
╭────────────────────────────────────────────────────────────╮
│ Export Summary                                             │
├────────────────────────────────────────────────────────────┤
│ Status:             ✓ Completed Successfully               │
│ Operation:          Export                                 │
│ Contact:            Alice Smith                            │
│ Messages Processed: 245                                    │
│ Duration:           3.45s                                  │
│ Speed:              71 msg/s                               │
╰────────────────────────────────────────────────────────────╯
```

**Features**:
- Status with icon and color
- Processing speed calculated
- Duration in seconds
- Message count with thousands separator

---

### 6. Execution Logs

#### Log Display Table
```
Execution Logs
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Level  ┃ Timestamp                 ┃ Message               ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ INFO   │ 2025-11-27T10:30:00      │ Initializing signal-  │
│        │                           │ cli interface         │
│ INFO   │ 2025-11-27T10:30:01      │ Using signal-cli      │
│        │                           │ version: 0.15.0       │
│ INFO   │ 2025-11-27T10:30:02      │ Found 42 contacts     │
│ DEBUG  │ 2025-11-27T10:30:03      │ Fetching messages for │
│        │                           │ +15551234567          │
│ INFO   │ 2025-11-27T10:30:05      │ Fetched 245 messages  │
│ INFO   │ 2025-11-27T10:30:06      │ Export successful to  │
│        │                           │ /path/to/export       │
└────────┴───────────────────────────┴───────────────────────┘

Total log entries: 6
```

**Features**:
- Color-coded by level:
  - DEBUG: dim
  - INFO: cyan
  - WARNING: yellow
  - ERROR: red
- ISO 8601 timestamps
- Clear, readable table format
- Total entry count

---

## User Experience Flow

### Typical Workflow

```
1. Authentication Check
   ↓
   [Spinner] Checking Signal authentication status...
   [Success] Green panel with auth details

2. Contact Selection
   ↓
   [Table] Display all contacts
   [Input] Prompt for search/number
   [Table] Filtered results
   [Panel] Contact preview
   [Confirm] Proceed? [y/N]

3. Message Fetching
   ↓
   [Spinner] Fetching messages from Signal database...
   ✓ Found 245 messages

4. Export Configuration
   ↓
   [Panel] Export Configuration
   [Confirm] Proceed with export? [y/N]

5. Export Execution
   ↓
   [Progress] Exporting messages... ▏████░░░░ 45%
   ✓ Exported to JSON format
   ✓ Exported to Markdown format
   ✓ Exported to HTML format
   ✓ Export manifest created

6. Summary
   ↓
   [Panel] Export Summary (green border)
   [Table] Execution Logs (--show-logs)

✓ Operation complete!
```

---

## Color Scheme

| Element | Color | Usage |
|---------|-------|-------|
| Success | Green | ✓ checkmarks, success panels |
| Error | Red | ✗ failures, error messages |
| Info | Cyan | Info text, column headers |
| Warning | Yellow | ⚠️ warnings, cautions |
| Highlight | Magenta | Table titles, section headers |
| Neutral | White | Main text |
| Subtle | Dim | Secondary info, UUIDs |

---

## Accessibility Features

1. **Clear Visual Hierarchy**
   - Panels for important sections
   - Tables for data organization
   - Icons for status (✓/✗)

2. **Non-Blocking Operations**
   - Spinners show progress without freezing
   - Progress bars update in real-time
   - No modal dialogs that trap input

3. **Readable Text**
   - Monospace font in panels
   - Proper spacing and alignment
   - Color used with text for clarity

4. **Helpful Prompts**
   - Clear instructions for each step
   - Examples in prompts
   - Suggestion of default values

5. **Error Messages**
   - Specific error descriptions
   - Actionable solutions
   - Error color (red) for visibility

---

## Advanced TUI Features

### Spinner Animation Styles
Available spinners (from Rich library):
- `dots` - ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
- `line` - ⠂ ⠐ ⠠ ⠈ ⠐
- `star` - ✶ ✸ ✹ ✺ ✹ ✷

Currently using: `dots` (most common)

### Progress Bar Customization
- Total vs. indeterminate progress
- Speed indicators (KB/s, msg/s)
- Download count display
- Percentage completion

### Panel Styles
- `heavy` - Thick borders
- `double` - Double-line borders
- `rounded` - Rounded corners (default)
- `square` - Square corners
- Color borders (green/red/yellow)

---

## Testing the TUI

### View All TUI Components

```bash
# Test contact selection and authentication check
sig-prune-contact --check-auth

# Test dry-run with full TUI (no side effects)
sig-prune-contact \
  --contact "+15551234567" \
  --dry-run \
  --format "json,md,html" \
  --show-logs

# Interactive contact selection
sig-prune-contact

# Full operation with summary
sig-prune-contact \
  --contact "+15551234567" \
  --format "json" \
  --show-logs \
  --verbose
```

### Visual Testing Checklist

- [ ] Contact table displays correctly
- [ ] Fuzzy search filters contacts
- [ ] Contact preview shows all fields
- [ ] Spinner animates during operations
- [ ] Progress bar updates smoothly
- [ ] Step indicators show in sequence
- [ ] Panels display with correct colors
- [ ] Confirmation dialogs are clear
- [ ] Error messages are readable
- [ ] Log table formats properly
- [ ] Colors are visible on terminal
- [ ] No text overlap or truncation

---

## Future Enhancements

Potential TUI improvements for future versions:

1. **Multi-task Display**
   - Live display of multiple operations
   - Side-by-side progress bars

2. **Interactive Lists**
   - Keyboard navigation for contacts
   - Up/down arrows to select
   - Space/Enter to confirm

3. **Live Metrics**
   - Real-time message count update
   - Live file size display
   - Database query progress

4. **Dashboard View**
   - Overview of all operations
   - Statistics summary
   - Export directory tree view

5. **Custom Themes**
   - Color scheme selection
   - Monochrome mode for accessibility
   - High-contrast theme

---

## Terminal Requirements

**Minimum**:
- 80x24 character terminal
- 16 colors support (basic ANSI colors)

**Recommended**:
- 120x40 character terminal
- 256 colors or true color support
- UTF-8 character encoding

**Tested**:
- Ubuntu Terminal
- macOS Terminal
- iTerm2
- Windows Terminal (WSL2)
- VS Code Terminal
- Alacritty

---

## Design Philosophy

The TUI is designed with these principles:

1. **User-First**: Clear guidance at every step
2. **Visual Feedback**: Never leave user wondering what's happening
3. **Professional**: Business-grade appearance and polish
4. **Accessible**: Works on various terminal types
5. **Non-Intrusive**: Information displayed without overwhelming
6. **Error-Aware**: Clear error messages with solutions

---

## Summary

The `sig-prune-contact` TUI provides a rich, professional terminal interface that:

- ✓ Guides users through multi-step workflows
- ✓ Provides real-time visual feedback
- ✓ Displays clear confirmation dialogs
- ✓ Shows operation summaries
- ✓ Displays execution logs on demand
- ✓ Handles errors gracefully
- ✓ Works across multiple terminal types

The result is a polished, professional CLI tool that's both powerful and easy to use.
