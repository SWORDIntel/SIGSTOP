"""Main CLI orchestrator for sig-prune-contact."""

import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .signal_cli import SignalCli, SignalCliError
from .tui import ContactSelector, ExportConfirmation, DeletionConfirmation, ProgressDisplay
from .export import MessageExporter, BackupChecker
from .deletion import DeletionManager
from .logger import set_logger_file, logger
from .utils import parse_contact_argument, expand_export_path, validate_formats, ensure_directory


@click.command()
@click.option(
    "--contact",
    type=str,
    default=None,
    help="Target contact (phone number or UUID). If omitted, interactive selection."
)
@click.option(
    "--export-dir",
    type=str,
    default="~/Documents/SWORD/sigexport2/signalchats",
    help="Base export directory."
)
@click.option(
    "--format",
    type=str,
    default="json",
    help="Export formats (comma-separated): json,md,html"
)
@click.option(
    "--attachments",
    is_flag=True,
    default=False,
    help="Export and copy attachments."
)
@click.option(
    "--delete",
    is_flag=True,
    default=False,
    help="Enable deletion after successful export."
)
@click.option(
    "--require-backup-check",
    is_flag=True,
    default=False,
    help="Require confirmation that backup exists before deletion."
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview only, no side effects."
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Skip interactive confirmations (batch mode)."
)
@click.option(
    "--leave-groups",
    is_flag=True,
    default=False,
    help="Also leave groups with this contact."
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging."
)
@click.option(
    "--log-file",
    type=str,
    default=None,
    help="Write structured logs to file."
)
def main(contact: Optional[str], export_dir: str, format: str, attachments: bool,
         delete: bool, require_backup_check: bool, dry_run: bool, force: bool,
         leave_groups: bool, verbose: bool, log_file: Optional[str]):
    """sig-prune-contact: Interactive Signal contact pruning and export tool."""

    console = Console()

    # Show banner
    console.print(Panel(
        f"[bold]sig-prune-contact v{__version__}[/bold]\nInteractive Signal contact pruning and export",
        style="bold blue"
    ))

    # Setup logging
    if log_file:
        set_logger_file(Path(log_file), verbose=verbose)
    else:
        # Still need to set logger with verbose flag
        from .logger import StructuredLogger
        import sig_prune_contact.logger as logger_module
        logger_module.logger = StructuredLogger(verbose=verbose)

    try:
        exit_code = _run_workflow(
            console=console,
            contact_arg=contact,
            export_dir=export_dir,
            formats=format,
            include_attachments=attachments,
            enable_deletion=delete,
            require_backup_check=require_backup_check,
            dry_run=dry_run,
            skip_confirmations=force,
            leave_groups=leave_groups,
            verbose=verbose
        )
        sys.exit(exit_code)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]", style="bold")
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def _run_workflow(console: Console, contact_arg: Optional[str], export_dir: str,
                 formats: str, include_attachments: bool, enable_deletion: bool,
                 require_backup_check: bool, dry_run: bool, skip_confirmations: bool,
                 leave_groups: bool, verbose: bool) -> int:
    """Run the main workflow.

    Returns:
        Exit code: 0 (success), 1 (export failed), 2 (export ok, delete failed)
    """
    # Initialize Signal CLI
    logger.info("Initializing signal-cli interface")
    try:
        signal_cli = SignalCli()
        signal_cli_version = signal_cli.get_version()
        logger.info(f"Using signal-cli version: {signal_cli_version}")
    except SignalCliError as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Failed to initialize signal-cli: {e}")
        return 1

    # Parse formats
    try:
        format_list = validate_formats(formats)
        logger.info(f"Export formats: {format_list}")
    except ValueError as e:
        console.print(f"[red]Invalid format: {e}[/red]")
        return 1

    # Expand export directory
    export_path = expand_export_path(export_dir)
    logger.info(f"Export directory: {export_path}")

    # Step 1: Contact selection
    console.print("\n[bold cyan]Step 1: Contact Selection[/bold cyan]")

    target_contact = None
    if contact_arg:
        # Direct contact argument
        parsed = parse_contact_argument(contact_arg)
        if parsed:
            logger.info(f"Using provided contact: {contact_arg}")
            # Find full contact info from list
            all_contacts = signal_cli.list_contacts()
            target_contact = _find_contact(all_contacts, parsed)
        else:
            console.print(f"[red]Invalid contact format: {contact_arg}[/red]")
            return 1
    else:
        # Interactive selection
        all_contacts = signal_cli.list_contacts()
        selector = ContactSelector(console=console)
        target_contact = selector.select_contact(all_contacts)

    if not target_contact:
        console.print("[yellow]No contact selected. Exiting.[/yellow]")
        logger.info("No contact selected, exiting")
        return 1

    logger.info(f"Selected contact: {target_contact.get('name')} ({target_contact.get('number')})")

    # Step 2: Fetch messages
    console.print("\n[bold cyan]Step 2: Fetching Messages[/bold cyan]")

    contact_id = target_contact.get("number") or target_contact.get("uuid")
    messages = signal_cli.fetch_messages(contact_id, dry_run=dry_run)
    console.print(f"[green]✓[/green] Found {len(messages)} messages")
    logger.info(f"Fetched {len(messages)} messages for {contact_id}")

    # Step 3: Export confirmation
    console.print("\n[bold cyan]Step 3: Export Configuration[/bold cyan]")

    export_confirm = ExportConfirmation(console=console)
    if not skip_confirmations:
        if not export_confirm.confirm_export(
            target_contact, str(export_path), format_list,
            include_attachments, len(messages), dry_run=dry_run
        ):
            console.print("[yellow]Export cancelled.[/yellow]")
            logger.info("Export cancelled by user")
            return 1

    # Step 4: Export messages
    console.print("\n[bold cyan]Step 4: Exporting Messages[/bold cyan]")

    exporter = MessageExporter(export_path)
    try:
        result_dir = exporter.export_messages(
            target_contact, messages, format_list,
            include_attachments=include_attachments,
            dry_run=dry_run
        )
        console.print(f"[green]✓[/green] Export complete: {result_dir}")
        logger.info(f"Export successful to {result_dir}")
    except Exception as e:
        console.print(f"[red]✗[/red] Export failed: {e}")
        logger.error(f"Export failed: {e}")
        return 1

    # If export was successful and not dry-run, we have the export dir
    if not dry_run and result_dir:
        export_dir_final = result_dir
    else:
        export_dir_final = None

    # Step 5: Deletion (if enabled)
    if enable_deletion:
        console.print("\n[bold cyan]Step 5: Deletion Phase[/bold cyan]")

        # Check for backup if required
        if require_backup_check:
            console.print("[yellow]Checking for backup...[/yellow]")
            backup_exists = BackupChecker.check_signal_backup() or BackupChecker.check_system_backup()
            if not backup_exists and not skip_confirmations:
                if not click.confirm("No backup found. Continue anyway?"):
                    console.print("[yellow]Deletion cancelled.[/yellow]")
                    logger.info("Deletion cancelled - no backup found")
                    return 0

        # Deletion confirmation
        date_range = _get_message_date_range(messages)
        attachment_count = sum(len(msg.get("attachments", [])) for msg in messages)

        del_confirm = DeletionConfirmation(console=console)
        if not skip_confirmations:
            if not del_confirm.confirm_deletion(
                target_contact, len(messages), attachment_count, date_range, dry_run=dry_run
            ):
                console.print("[yellow]Deletion cancelled.[/yellow]")
                logger.info("Deletion cancelled by user")
                return 0

        # Perform deletion
        if not export_dir_final:
            console.print("[red]Cannot delete without export directory. Use non-dry-run mode.[/red]")
            return 2

        deletion_manager = DeletionManager(signal_cli)
        if deletion_manager.delete_conversation(
            target_contact, export_dir_final, leave_groups=leave_groups, dry_run=dry_run
        ):
            del_confirm.show_deletion_result(True, target_contact.get("name"))
            logger.info(f"Deletion successful for {target_contact.get('name')}")
            console.print("[green]✓[/green] Operation complete!")
            return 0
        else:
            del_confirm.show_deletion_result(False, target_contact.get("name"))
            logger.error(f"Deletion failed for {target_contact.get('name')}")
            console.print("[red]✗[/red] Deletion failed (export was successful)")
            return 2

    else:
        # Export only
        console.print("\n[green]✓ Export complete (deletion not enabled)[/green]")
        logger.info("Export completed without deletion")
        return 0


def _find_contact(contacts: List[dict], parsed: dict) -> Optional[dict]:
    """Find contact from list by number or UUID.

    Args:
        contacts: List of contact dicts
        parsed: Dict with 'number' or 'uuid' key

    Returns:
        Full contact dict or None
    """
    if "number" in parsed:
        number = parsed["number"]
        for contact in contacts:
            if contact.get("number") == number:
                return contact
    elif "uuid" in parsed:
        uuid = parsed["uuid"]
        for contact in contacts:
            if contact.get("uuid") == uuid:
                return contact

    return None


def _get_message_date_range(messages: List[dict]) -> tuple:
    """Get date range from messages.

    Returns:
        Tuple of (start_date, end_date) strings or (None, None)
    """
    if not messages:
        return (None, None)

    dates = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
    if not dates:
        return (None, None)

    dates.sort()
    return (dates[0], dates[-1])


if __name__ == "__main__":
    main()
