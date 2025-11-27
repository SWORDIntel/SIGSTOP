"""TUI (Text User Interface) components for sig-prune-contact."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fuzzywuzzy import process as fuzzy_process
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn
from rich.live import Live
from rich.layout import Layout
import json

from .logger import logger


class ContactSelector:
    """Interactive contact selection with fuzzy search."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize selector.

        Args:
            console: Rich console for output
        """
        self.console = console or Console()

    def select_contact(self, contacts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Interactively select a contact.

        Args:
            contacts: List of contact dicts

        Returns:
            Selected contact or None if cancelled
        """
        if not contacts:
            self.console.print("[red]No contacts found[/red]")
            return None

        self.console.print(f"\n[bold]Found {len(contacts)} contacts[/bold]\n")

        # Show initial table
        self._display_contacts_table(contacts)

        # Get search query
        search_query = Prompt.ask(
            "[bold]Search contacts[/bold] (name or number, or leave blank to see all)",
            default=""
        ).strip()

        filtered = contacts
        if search_query:
            filtered = self._fuzzy_search_contacts(contacts, search_query)
            if not filtered:
                self.console.print(f"[yellow]No contacts match '{search_query}'[/yellow]")
                return None

            self.console.print(f"\n[bold]Filtered: {len(filtered)} contacts[/bold]\n")
            self._display_contacts_table(filtered)

        # Select from filtered
        while True:
            choice = Prompt.ask(
                "[bold]Enter contact number[/bold] (1-{})".format(len(filtered))
            )

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(filtered):
                    contact = filtered[idx]
                    self._show_contact_preview(contact)

                    if Confirm.ask("[bold]Proceed with this contact?[/bold]"):
                        return contact
                    else:
                        return self.select_contact(contacts)  # Retry
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number[/red]")

    def _display_contacts_table(self, contacts: List[Dict[str, Any]]):
        """Display contacts in a formatted table."""
        table = Table(title="Signal Contacts")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Number", style="green")
        table.add_column("UUID", style="dim")

        for idx, contact in enumerate(contacts, 1):
            uuid = contact.get("uuid", "—")
            if uuid and len(uuid) > 16:
                uuid = uuid[:8] + "..." + uuid[-8:]

            table.add_row(
                str(idx),
                contact.get("name", "—"),
                contact.get("number", "—"),
                uuid
            )

        self.console.print(table)

    @staticmethod
    def _fuzzy_search_contacts(contacts: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Fuzzy search contacts by name or number."""
        # Create searchable keys
        searchable = []
        for contact in contacts:
            name = contact.get("name", "")
            number = contact.get("number", "")
            searchable.append(f"{name} {number}")

        # Perform fuzzy search
        matches = fuzzy_process.extract(query, searchable, limit=None, score_cutoff=60)
        matched_indices = [idx for _, _, idx in matches]

        return [contacts[idx] for idx in matched_indices]

    def _show_contact_preview(self, contact: Dict[str, Any]):
        """Show a preview of selected contact."""
        preview_data = {
            "Name": contact.get("name", "—"),
            "Number": contact.get("number", "—"),
            "UUID": contact.get("uuid", "—")
        }

        panel = Panel(
            "\n".join(f"[bold]{k}:[/bold] {v}" for k, v in preview_data.items()),
            title="[bold]Contact Preview[/bold]",
            expand=False
        )
        self.console.print(panel)


class ExportConfirmation:
    """Confirmation UI for export phase."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize confirmation UI."""
        self.console = console or Console()

    def confirm_export(self, contact: Dict[str, Any], export_dir: str,
                      formats: List[str], include_attachments: bool,
                      message_count: int, dry_run: bool = False) -> bool:
        """Confirm export settings before proceeding.

        Returns:
            True to proceed, False to cancel
        """
        details = {
            "Contact": f"{contact.get('name')} ({contact.get('number')})",
            "Export Directory": export_dir,
            "Formats": ", ".join(formats),
            "Attachments": "Yes" if include_attachments else "No",
            "Messages to Export": message_count,
            "Mode": "DRY RUN" if dry_run else "LIVE"
        }

        panel_text = "\n".join(
            f"[bold]{k}:[/bold] {v}" for k, v in details.items()
        )

        self.console.print(Panel(panel_text, title="[bold]Export Configuration[/bold]"))

        return Confirm.ask("[bold]Proceed with export?[/bold]")


class DeletionConfirmation:
    """Confirmation UI for deletion phase."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize deletion confirmation."""
        self.console = console or Console()

    def confirm_deletion(self, contact: Dict[str, Any], message_count: int,
                        attachment_count: int, date_range: tuple,
                        dry_run: bool = False) -> bool:
        """Confirm deletion with summary.

        Args:
            contact: Contact being deleted
            message_count: Number of messages
            attachment_count: Number of attachments
            date_range: Tuple of (start_date, end_date)
            dry_run: If True, not actually deleting

        Returns:
            True to proceed, False to cancel
        """
        start_date, end_date = date_range
        contact_slug = self._slugify(contact.get("name", "contact"))

        summary = {
            "Messages": message_count,
            "Attachments": attachment_count,
            "Date Range": f"{start_date} to {end_date}",
            "Contact": f"{contact.get('name')} ({contact.get('number')})",
            "Mode": "DRY RUN" if dry_run else "LIVE DELETION"
        }

        panel_text = "\n".join(f"[bold]{k}:[/bold] {v}" for k, v in summary.items())
        self.console.print(Panel(
            panel_text,
            title="[bold red]⚠️  DELETION SUMMARY[/bold red]",
            expand=False
        ))

        # Require explicit confirmation
        self.console.print(
            f"\n[bold yellow]Type the contact name to confirm deletion:[/bold yellow] {contact_slug}"
        )

        confirmation = Prompt.ask("Confirmation")

        if confirmation.strip().lower() == contact_slug.lower():
            return True

        self.console.print("[red]Deletion cancelled[/red]")
        return False

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to slug."""
        return text.lower().replace(" ", "-")

    def show_deletion_result(self, success: bool, contact_name: str):
        """Show deletion result."""
        if success:
            self.console.print(
                Panel(
                    f"[green]✓ Conversation with {contact_name} deleted successfully[/green]",
                    title="[bold]Deletion Complete[/bold]"
                )
            )
        else:
            self.console.print(
                Panel(
                    f"[red]✗ Failed to delete conversation with {contact_name}[/red]",
                    title="[bold]Deletion Failed[/bold]"
                )
            )


class OperationStatus:
    """Display real-time operation status with spinner."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize status display."""
        self.console = console or Console()
        self.progress = None

    def start_operation(self, operation: str):
        """Start an operation with spinner."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        self.progress.start()
        self.task_id = self.progress.add_task(operation, total=None)

    def update_operation(self, status: str):
        """Update operation status."""
        if self.progress:
            self.progress.update(self.task_id, description=status)

    def complete_operation(self, success: bool = True):
        """Complete operation and show result."""
        if self.progress:
            symbol = "[green]✓[/green]" if success else "[red]✗[/red]"
            desc = self.progress._tasks[self.task_id].description
            self.progress.stop()
            self.console.print(f"{symbol} {desc}")
            self.progress = None


class ProgressDisplay:
    """Display progress during export/deletion with progress bars."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize progress display."""
        self.console = console or Console()
        self.progress = None

    def start_progress(self, total: int, description: str = "Processing"):
        """Start a progress bar."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=self.console
        )
        self.progress.start()
        self.task_id = self.progress.add_task(description, total=total)

    def update_progress(self, advance: int = 1):
        """Advance progress bar."""
        if self.progress:
            self.progress.update(self.task_id, advance=advance)

    def finish_progress(self, success: bool = True):
        """Finish progress bar."""
        if self.progress:
            self.progress.stop()
            self.progress = None

    def show_export_progress(self, current: int, total: int, phase: str):
        """Show export progress in simple format."""
        percent = (current / total * 100) if total > 0 else 0
        self.console.print(
            f"[cyan]{phase}:[/cyan] {current}/{total} ({percent:.1f}%)"
        )

    def show_step(self, step: str, success: bool = True):
        """Show a step completion."""
        symbol = "[green]✓[/green]" if success else "[red]✗[/red]"
        self.console.print(f"{symbol} {step}")


class ManifestDisplay:
    """Display export manifest."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize manifest display."""
        self.console = console or Console()

    def display_manifest(self, manifest: Dict[str, Any]):
        """Display export manifest in readable format."""
        manifest_json = json.dumps(manifest, indent=2)
        syntax = Syntax(manifest_json, "json", theme="monokai", line_numbers=False)

        self.console.print(Panel(
            syntax,
            title="[bold]Export Manifest[/bold]"
        ))

    def display_summary(self, manifest: Dict[str, Any]):
        """Display manifest summary in human-readable format."""
        contact = manifest.get("contact", {})
        stats = manifest.get("statistics", {})
        config = manifest.get("export_config", {})

        summary_lines = [
            f"[bold cyan]Contact:[/bold cyan] {contact.get('name')} ({contact.get('number')})",
            f"[bold cyan]Messages:[/bold cyan] {stats.get('message_count', 0)}",
            f"[bold cyan]Attachments:[/bold cyan] {stats.get('attachment_count', 0)}",
            f"[bold cyan]Date Range:[/bold cyan] {stats.get('date_range', {}).get('start', 'N/A')} to {stats.get('date_range', {}).get('end', 'N/A')}",
            f"[bold cyan]Formats:[/bold cyan] {', '.join(config.get('formats', []))}",
            f"[bold cyan]Export Date:[/bold cyan] {manifest.get('export_date', 'N/A')}",
        ]

        self.console.print(Panel(
            "\n".join(summary_lines),
            title="[bold green]✓ Export Summary[/bold green]",
            border_style="green"
        ))


class SummaryDisplay:
    """Display operation summary and statistics."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize summary display."""
        self.console = console or Console()

    def show_operation_summary(self, operation_type: str, contact_name: str,
                              message_count: int, duration_seconds: float,
                              success: bool = True):
        """Display summary of completed operation."""
        status_color = "green" if success else "red"
        status_icon = "✓" if success else "✗"
        status_text = "Completed Successfully" if success else "Failed"

        summary_data = {
            "Status": f"[{status_color}]{status_icon} {status_text}[/{status_color}]",
            "Operation": operation_type,
            "Contact": contact_name,
            "Messages Processed": f"{message_count:,}",
            "Duration": f"{duration_seconds:.2f}s",
            "Speed": f"{message_count / duration_seconds:.0f} msg/s" if duration_seconds > 0 else "N/A"
        }

        summary_lines = [
            f"[bold]{k}:[/bold] {v}" for k, v in summary_data.items()
        ]

        self.console.print(Panel(
            "\n".join(summary_lines),
            title=f"[bold]{operation_type} Summary[/bold]",
            border_style=status_color
        ))

    def show_statistics_table(self, stats: Dict[str, Any]):
        """Display statistics in table format."""
        table = Table(title="Operation Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        for key, value in stats.items():
            table.add_row(key, str(value))

        self.console.print(table)
