"""TUI (Text User Interface) components for sig-prune-contact."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fuzzywuzzy import process as fuzzy_process
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
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


class ProgressDisplay:
    """Display progress during export/deletion."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize progress display."""
        self.console = console or Console()

    def show_export_progress(self, current: int, total: int, phase: str):
        """Show export progress."""
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
