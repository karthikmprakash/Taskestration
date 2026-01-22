#!/usr/bin/env python3
"""Register a new automation."""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli import CLITheme, print_error, print_info, print_success, print_warning
from src.registry import AutomationRegistry

console = Console()


@click.command()
@click.argument("name")
@click.option(
    "-d",
    "--description",
    default="",
    help="Description of the automation",
    show_default=True,
)
@click.option(
    "-c",
    "--cron",
    help="CRON schedule expression (e.g., '0 9 * * *' for daily at 9 AM)",
)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["python", "shell"], case_sensitive=False),
    help="Script type (will be auto-detected if script exists)",
)
@click.option(
    "--automations-dir",
    type=click.Path(path_type=Path),
    default=Path(__file__).parent.parent / "automations",
    help="Directory containing automations",
    show_default=True,
)
def main(name: str, description: str, cron: str | None, type: str | None, automations_dir: Path):
    """Register a new automation with beautiful CLI output."""
    # Print header
    console.print()
    console.print(
        Panel(
            f"[bold {CLITheme.ACCENT}]Registering Automation[/bold {CLITheme.ACCENT}]",
            border_style=CLITheme.ACCENT,
            padding=(1, 2),
        )
    )
    console.print()

    try:
        registry = AutomationRegistry(automations_dir)
        automation_dir = automations_dir / name

        # Show registration info
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column(style=CLITheme.MUTED, width=15)
        info_table.add_column(style=CLITheme.HIGHLIGHT)
        info_table.add_row("Name:", name)
        info_table.add_row("Directory:", str(automation_dir))
        if description:
            info_table.add_row("Description:", description)
        if cron:
            info_table.add_row("Schedule:", f"[{CLITheme.INFO}]{cron}[/{CLITheme.INFO}]")
        if type:
            info_table.add_row("Type:", f"[{CLITheme.ACCENT}]{type}[/{CLITheme.ACCENT}]")

        console.print(info_table)
        console.print()

        # Register automation
        automation = registry.register_automation(
            automation_dir=automation_dir,
            name=name,
            description=description,
            cron_schedule=cron,
            script_type=type,
        )

        # Show results
        if automation.config.script_path:
            print_success(f"Found script: {automation.config.script_path.name}")
        else:
            print_warning(
                "No script found. Please add run.py or run.sh to the automation directory."
            )

        console.print()
        print_success("Automation registered successfully!", icon=True)

        # Show next steps
        console.print()
        next_steps = Panel(
            f"[{CLITheme.INFO}]To enable/disable or modify schedule, edit:[/{CLITheme.INFO}]\n"
            f"[{CLITheme.HIGHLIGHT}]{automation_dir / 'config.yaml'}[/{CLITheme.HIGHLIGHT}]",
            title="[bold]Next Steps[/bold]",
            border_style=CLITheme.INFO,
            padding=(1, 2),
        )
        console.print(next_steps)

    except Exception as e:
        console.print()
        print_error(f"Failed to register automation: {e}")
        raise click.Abort()


if __name__ == "__main__":
    main()
