"""CLI styling and theme utilities."""

from datetime import datetime
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Global console instance
console = Console()


class CLITheme:
    """Color theme for CLI output."""

    # Status colors
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"
    MUTED = "dim white"

    # Status icons
    SUCCESS_ICON = "✓"
    ERROR_ICON = "✗"
    WARNING_ICON = "⚠"
    INFO_ICON = "ℹ"
    SKIP_ICON = "⊘"

    # Accent colors
    ACCENT = "cyan"
    HIGHLIGHT = "bright_white"
    SECONDARY = "bright_black"


class AutomationStatus(Enum):
    """Automation status types."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    DISABLED = "disabled"
    ENABLED = "enabled"
    PENDING = "pending"


def get_status_style(status: AutomationStatus) -> tuple[str, str]:
    """Get color and icon for a status."""
    styles = {
        AutomationStatus.SUCCESS: (CLITheme.SUCCESS, CLITheme.SUCCESS_ICON),
        AutomationStatus.FAILED: (CLITheme.ERROR, CLITheme.ERROR_ICON),
        AutomationStatus.SKIPPED: (CLITheme.WARNING, CLITheme.SKIP_ICON),
        AutomationStatus.DISABLED: (CLITheme.MUTED, CLITheme.WARNING_ICON),
        AutomationStatus.ENABLED: (CLITheme.SUCCESS, CLITheme.SUCCESS_ICON),
        AutomationStatus.PENDING: (CLITheme.INFO, CLITheme.INFO_ICON),
    }
    return styles.get(status, (CLITheme.MUTED, "?"))


def print_success(message: str, icon: bool = True) -> None:
    """Print a success message."""
    prefix = f"{CLITheme.SUCCESS_ICON} " if icon else ""
    console.print(f"{prefix}[{CLITheme.SUCCESS}]{message}[/{CLITheme.SUCCESS}]")


def print_error(message: str, icon: bool = True) -> None:
    """Print an error message."""
    prefix = f"{CLITheme.ERROR_ICON} " if icon else ""
    console.print(f"{prefix}[{CLITheme.ERROR}]{message}[/{CLITheme.ERROR}]")


def print_warning(message: str, icon: bool = True) -> None:
    """Print a warning message."""
    prefix = f"{CLITheme.WARNING_ICON} " if icon else ""
    console.print(f"{prefix}[{CLITheme.WARNING}]{message}[/{CLITheme.WARNING}]")


def print_info(message: str, icon: bool = True) -> None:
    """Print an info message."""
    prefix = f"{CLITheme.INFO_ICON} " if icon else ""
    console.print(f"{prefix}[{CLITheme.INFO}]{message}[/{CLITheme.INFO}]")


def print_header(title: str, subtitle: str | None = None) -> None:
    """Print a styled header."""
    text = Text(title, style=f"bold {CLITheme.ACCENT}")
    if subtitle:
        text.append(f"\n{subtitle}", style=CLITheme.MUTED)
    console.print(Panel(text, border_style=CLITheme.ACCENT, padding=(1, 2)))


def create_status_table(title: str = "Automations") -> Table:
    """Create a styled table for automation status."""
    table = Table(title=title, show_header=True, header_style=f"bold {CLITheme.ACCENT}")
    table.add_column("Status", style="dim", width=8)
    table.add_column("Name", style=CLITheme.HIGHLIGHT, width=20)
    table.add_column("Description", style=CLITheme.MUTED, width=40)
    table.add_column("Schedule", style=CLITheme.SECONDARY, width=20)
    return table


def create_result_table(title: str = "Execution Results") -> Table:
    """Create a styled table for execution results."""
    table = Table(title=title, show_header=True, header_style=f"bold {CLITheme.ACCENT}")
    table.add_column("Status", style="dim", width=8)
    table.add_column("Automation", style=CLITheme.HIGHLIGHT, width=20)
    table.add_column("Time", style=CLITheme.SECONDARY, width=12)
    table.add_column("Exit Code", style=CLITheme.SECONDARY, width=10)
    table.add_column("Details", style=CLITheme.MUTED, width=30)
    return table


def create_schedule_table(title: str = "Upcoming Scheduled Executions") -> Table:
    """Create a styled table for scheduled executions."""
    table = Table(title=title, show_header=True, header_style=f"bold {CLITheme.ACCENT}")
    table.add_column("Automation", style=CLITheme.HIGHLIGHT, width=20)
    table.add_column("Next Run", style=CLITheme.INFO, width=20)
    table.add_column("Time Until", style=CLITheme.SUCCESS, width=15)
    table.add_column("Schedule", style=CLITheme.SECONDARY, width=20)
    table.add_column("Type", style=CLITheme.MUTED, width=10)
    return table


def format_time_until(next_run: datetime, now: datetime) -> tuple[str, str]:
    """Format time until next run with color."""
    time_until = next_run - now
    total_seconds = time_until.total_seconds()

    if total_seconds < 0:
        return "OVERDUE", CLITheme.ERROR
    elif total_seconds < 60:
        seconds = int(total_seconds)
        return f"in {seconds}s", CLITheme.WARNING
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"in {minutes}m {seconds}s", CLITheme.INFO
    else:
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"in {hours}h {minutes}m", CLITheme.SUCCESS
