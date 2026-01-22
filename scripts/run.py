#!/usr/bin/env python3
"""Run automations."""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from src.cli import (
    AutomationStatus,
    CLITheme,
    create_result_table,
    create_schedule_table,
    create_status_table,
    get_status_style,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from src.registry import AutomationRegistry
from src.runners import RunnerFactory
from src.scheduler import AutomationScheduler, GlobalConfig

console = Console()


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


def print_result(automation_name: str, result, verbose: bool = False):
    """Print execution result with rich formatting."""
    status_map = {
        "success": AutomationStatus.SUCCESS,
        "failed": AutomationStatus.FAILED,
        "skipped": AutomationStatus.SKIPPED,
    }

    status = status_map.get(result.status.value, AutomationStatus.PENDING)
    color, icon = get_status_style(status)

    status_text = f"[{color}]{icon} {automation_name}: {result.status.value.upper()}[/{color}]"
    console.print(status_text)

    if verbose:
        details = []
        if result.execution_time > 0:
            details.append(f"Execution time: [{CLITheme.INFO}]{result.execution_time:.2f}s[/{CLITheme.INFO}]")
        if result.exit_code != 0:
            details.append(f"Exit code: [{CLITheme.ERROR}]{result.exit_code}[/{CLITheme.ERROR}]")

        if details:
            console.print(f"  {' | '.join(details)}", style=CLITheme.MUTED)

        if result.output:
            console.print()
            console.print(f"  [{CLITheme.INFO}]Output:[/{CLITheme.INFO}]")
            console.print(Panel(result.output, border_style=CLITheme.INFO, padding=(0, 1)))

        if result.error:
            console.print()
            console.print(f"  [{CLITheme.ERROR}]Error:[/{CLITheme.ERROR}]")
            console.print(Panel(result.error, border_style=CLITheme.ERROR, padding=(0, 1)))


@click.command()
@click.argument("automation", required=False)
@click.option("--all", "run_all", is_flag=True, help="Run all enabled automations")
@click.option("--use-global", is_flag=True, help="Use global CRON schedule for all automations")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
@click.option("--schedule", is_flag=True, help="List upcoming scheduled executions")
@click.option("--limit", type=int, help="Limit number of upcoming executions to show")
@click.option(
    "--automations-dir",
    type=click.Path(path_type=Path),
    default=Path(__file__).parent.parent / "automations",
    help="Directory containing automations",
    show_default=True,
)
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(__file__).parent.parent / "config",
    help="Directory containing global config",
    show_default=True,
)
def main(
    automation: str | None,
    run_all: bool,
    use_global: bool,
    verbose: bool,
    output_json: bool,
    schedule: bool,
    limit: int | None,
    automations_dir: Path,
    config_dir: Path,
):
    """Run automations with beautiful CLI output."""
    # Load global config
    config_path = config_dir / "global.yaml"
    global_config = GlobalConfig.load(config_path)

    # Initialize components
    registry = AutomationRegistry(automations_dir)
    runner_factory = RunnerFactory()
    scheduler = AutomationScheduler(global_config, runner_factory)

    # Discover automations
    automations = registry.discover_automations()

    if not automations:
        console.print()
        print_warning("No automations found.")
        return 1

    # Handle schedule listing
    if schedule:
        console.print()
        console.print(
            Panel(
                f"[bold {CLITheme.ACCENT}]Upcoming Scheduled Executions[/bold {CLITheme.ACCENT}]",
                border_style=CLITheme.ACCENT,
                padding=(1, 2),
            )
        )
        console.print()

        upcoming = scheduler.get_upcoming_executions(automations, limit=limit)

        if not upcoming:
            print_info("No scheduled executions found.")
            print_info("Make sure automations have CRON schedules configured.")
            return 0

        if output_json:
            output = [
                {
                    "automation": exec.automation.name,
                    "next_run_time": exec.next_run_time.isoformat(),
                    "cron_schedule": exec.cron_schedule,
                    "is_using_global": exec.is_using_global,
                }
                for exec in upcoming
            ]
            console.print(json.dumps(output, indent=2))
        else:
            table = create_schedule_table()
            now = datetime.now()

            for exec in upcoming:
                time_str, time_color = format_time_until(exec.next_run_time, now)
                schedule_type = "global" if exec.is_using_global else "local"
                schedule_type_color = CLITheme.INFO if exec.is_using_global else CLITheme.ACCENT

                table.add_row(
                    exec.automation.name,
                    exec.next_run_time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"[{time_color}]{time_str}[/{time_color}]",
                    exec.cron_schedule,
                    f"[{schedule_type_color}]{schedule_type}[/{schedule_type_color}]",
                )

            console.print(table)

        return 0

    results = {}

    if automation:
        # Run specific automation
        automation_obj = next((a for a in automations if a.name == automation), None)

        if not automation_obj:
            console.print()
            print_error(f"Automation '{automation}' not found.")
            console.print()
            print_info("Available automations:")
            for a in automations:
                console.print(f"  [{CLITheme.ACCENT}]{a.name}[/{CLITheme.ACCENT}]")
            return 1

        # Show header
        console.print()
        console.print(
            Panel(
                f"[bold {CLITheme.ACCENT}]Running Automation[/bold {CLITheme.ACCENT}]\n"
                f"[{CLITheme.HIGHLIGHT}]{automation_obj.name}[/{CLITheme.HIGHLIGHT}]",
                border_style=CLITheme.ACCENT,
                padding=(1, 2),
            )
        )
        console.print()

        # Run with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {automation_obj.name}...", total=None)
            result = scheduler.run_automation(automation_obj)
            progress.update(task, completed=True)

        results[automation_obj.name] = result

        console.print()

        if not output_json:
            print_result(automation_obj.name, result, verbose)
        else:
            console.print(
                json.dumps(
                    {
                        automation_obj.name: {
                            "status": result.status.value,
                            "exit_code": result.exit_code,
                            "execution_time": result.execution_time,
                            "output": result.output,
                            "error": result.error,
                        }
                    },
                    indent=2,
                )
            )

    elif run_all:
        # Run all enabled automations
        console.print()
        console.print(
            Panel(
                f"[bold {CLITheme.ACCENT}]Running All Enabled Automations[/bold {CLITheme.ACCENT}]",
                border_style=CLITheme.ACCENT,
                padding=(1, 2),
            )
        )
        console.print()

        enabled_count = sum(1 for a in automations if a.enabled)
        if enabled_count == 0:
            print_warning("No enabled automations found.")
            return 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {enabled_count} automation(s)...", total=None)
            results = scheduler.run_all_enabled(automations)
            progress.update(task, completed=True)

        console.print()

        if not output_json:
            if verbose:
                for name, result in results.items():
                    print_result(name, result, verbose)
                    console.print()
            else:
                table = create_result_table()
                for name, result in results.items():
                    status_map = {
                        "success": AutomationStatus.SUCCESS,
                        "failed": AutomationStatus.FAILED,
                        "skipped": AutomationStatus.SKIPPED,
                    }
                    status = status_map.get(result.status.value, AutomationStatus.PENDING)
                    color, icon = get_status_style(status)

                    details = []
                    if result.error:
                        details.append("Error occurred")
                    elif result.output:
                        details.append("Completed")

                    table.add_row(
                        f"[{color}]{icon} {result.status.value.upper()}[/{color}]",
                        name,
                        f"{result.execution_time:.2f}s" if result.execution_time > 0 else "N/A",
                        str(result.exit_code),
                        ", ".join(details) if details else "OK",
                    )

                console.print(table)
        else:
            output_dict: dict[str, dict[str, object]] = {
                name: {
                    "status": result.status.value,
                    "exit_code": result.exit_code,
                    "execution_time": result.execution_time,
                    "output": result.output,
                    "error": result.error,
                }
                for name, result in results.items()
            }
            console.print(json.dumps(output_dict, indent=2))

    else:
        # List automations
        console.print()
        console.print(
            Panel(
                f"[bold {CLITheme.ACCENT}]Available Automations[/bold {CLITheme.ACCENT}]",
                border_style=CLITheme.ACCENT,
                padding=(1, 2),
            )
        )
        console.print()

        table = create_status_table()
        for automation_obj in automations:
            status = AutomationStatus.ENABLED if automation_obj.enabled else AutomationStatus.DISABLED
            color, icon = get_status_style(status)

            schedule = scheduler.get_effective_schedule(automation_obj)
            schedule_str = schedule if schedule else "global/default"
            schedule_color = CLITheme.INFO if schedule else CLITheme.MUTED

            description = automation_obj.config.description or "No description"

            table.add_row(
                f"[{color}]{icon} {status.value.upper()}[/{color}]",
                automation_obj.name,
                description,
                f"[{schedule_color}]{schedule_str}[/{schedule_color}]",
            )

        console.print(table)

    # Return exit code based on results
    if results:
        failed = any(r.status.value == "failed" for r in results.values())
        if failed:
            console.print()
            print_error("Some automations failed!")
        else:
            console.print()
            print_success("All automations completed successfully!")
        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
