#!/usr/bin/env python3
"""Interactive CLI menu for automation management."""

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.cli import (
    AutomationStatus,
    CLITheme,
    create_result_table,
    create_schedule_table,
    create_status_table,
    format_time_until,
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


class InteractiveCLI:
    """Interactive CLI menu system."""

    def __init__(self, automations_dir: Path, config_dir: Path):
        """Initialize the interactive CLI."""
        self.automations_dir = automations_dir
        self.config_dir = config_dir

        # Load global config
        config_path = config_dir / "global.yaml"
        self.global_config = GlobalConfig.load(config_path)

        # Initialize components
        self.registry = AutomationRegistry(automations_dir)
        self.runner_factory = RunnerFactory()
        self.scheduler = AutomationScheduler(self.global_config, self.runner_factory)

    def clear_screen(self):
        """Clear the console screen."""
        console.clear()

    def show_header(self, title: str, subtitle: str | None = None):
        """Show a header panel."""
        text = f"[bold {CLITheme.ACCENT}]{title}[/bold {CLITheme.ACCENT}]"
        if subtitle:
            text += f"\n[{CLITheme.MUTED}]{subtitle}[/{CLITheme.MUTED}]"
        console.print()
        console.print(Panel(text, border_style=CLITheme.ACCENT, padding=(1, 2)))
        console.print()

    def show_main_menu(self):
        """Show the main menu."""
        self.clear_screen()
        self.show_header("Automation Control Panel", "Interactive Menu")

        menu_options = [
            ("1", "View All Automations", self.view_automations),
            ("2", "Run Automation", self.run_automation_menu),
            ("3", "Run All Enabled Automations", self.run_all_automations),
            ("4", "View Scheduled Executions", self.view_schedules),
            ("5", "Register New Automation", self.register_automation_menu),
            ("6", "Automation Details", self.view_automation_details),
            ("q", "Quit", None),
        ]

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style=CLITheme.ACCENT, width=4)
        table.add_column(style=CLITheme.HIGHLIGHT)

        for key, label, _ in menu_options:
            table.add_row(f"[{CLITheme.ACCENT}]{key}[/{CLITheme.ACCENT}]", label)

        console.print(table)
        console.print()

        choice = Prompt.ask(
            "Select an option",
            choices=[opt[0] for opt in menu_options],
            default="1",
        )

        # Find and execute the selected action
        for key, _, action in menu_options:
            if choice == key:
                if action:
                    return action()
                else:  # Quit
                    return False

        return True

    def view_automations(self):
        """View all automations in a table."""
        self.clear_screen()
        self.show_header("All Automations")

        automations = self.registry.discover_automations()

        if not automations:
            print_warning("No automations found.")
            Prompt.ask("\nPress Enter to continue", default="")
            return True

        table = create_status_table()
        for automation in automations:
            status = AutomationStatus.ENABLED if automation.enabled else AutomationStatus.DISABLED
            color, icon = get_status_style(status)

            schedule = self.scheduler.get_effective_schedule(automation)
            schedule_str = schedule if schedule else "global/default"
            schedule_color = CLITheme.INFO if schedule else CLITheme.MUTED

            description = automation.config.description or "No description"

            table.add_row(
                f"[{color}]{icon} {status.value.upper()}[/{color}]",
                automation.name,
                description,
                f"[{schedule_color}]{schedule_str}[/{schedule_color}]",
            )

        console.print(table)
        console.print()
        Prompt.ask("Press Enter to continue", default="")
        return True

    def run_automation_menu(self):
        """Menu for running a specific automation."""
        self.clear_screen()
        self.show_header("Run Automation")

        automations = self.registry.discover_automations()

        if not automations:
            print_warning("No automations found.")
            Prompt.ask("\nPress Enter to continue", default="")
            return True

        # Create selection list
        choices = [f"{i+1}" for i in range(len(automations))]
        choices.append("b")  # Back option

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style=CLITheme.ACCENT, width=4)
        table.add_column(style=CLITheme.HIGHLIGHT, width=25)
        table.add_column(style=CLITheme.MUTED)

        for i, automation in enumerate(automations):
            status_icon = "✓" if automation.enabled else "⊘"
            status_color = CLITheme.SUCCESS if automation.enabled else CLITheme.MUTED
            table.add_row(
                f"[{CLITheme.ACCENT}]{i+1}[/{CLITheme.ACCENT}]",
                f"[{status_color}]{status_icon}[/{status_color}] {automation.name}",
                automation.config.description or "No description",
            )

        table.add_row(f"[{CLITheme.ACCENT}]b[/{CLITheme.ACCENT}]", "[dim]Back to main menu[/dim]", "")

        console.print(table)
        console.print()

        choice = Prompt.ask("Select automation to run", choices=choices, default="b")

        if choice == "b":
            return True

        try:
            index = int(choice) - 1
            if 0 <= index < len(automations):
                automation = automations[index]
                return self.run_automation(automation)
        except (ValueError, IndexError):
            print_error("Invalid selection.")
            Prompt.ask("\nPress Enter to continue", default="")

        return True

    def run_automation(self, automation):
        """Run a specific automation."""
        self.clear_screen()
        self.show_header(f"Running: {automation.name}")

        if not automation.enabled:
            print_warning(f"Automation '{automation.name}' is disabled.")
            if not Confirm.ask("Do you want to run it anyway?"):
                Prompt.ask("\nPress Enter to continue", default="")
                return True

        console.print(f"Executing [bold {CLITheme.ACCENT}]{automation.name}[/bold {CLITheme.ACCENT}]...")
        console.print()

        # Run automation
        result = self.scheduler.run_automation(automation)

        # Show results
        status_map = {
            "success": AutomationStatus.SUCCESS,
            "failed": AutomationStatus.FAILED,
            "skipped": AutomationStatus.SKIPPED,
        }
        status = status_map.get(result.status.value, AutomationStatus.PENDING)
        color, icon = get_status_style(status)

        console.print()
        status_text = f"[{color}]{icon} {automation.name}: {result.status.value.upper()}[/{color}]"
        console.print(status_text)

        if result.execution_time > 0:
            console.print(f"  Execution time: [{CLITheme.INFO}]{result.execution_time:.2f}s[/{CLITheme.INFO}]")
        if result.exit_code != 0:
            console.print(f"  Exit code: [{CLITheme.ERROR}]{result.exit_code}[/{CLITheme.ERROR}]")

        if result.output:
            console.print()
            console.print(f"  [{CLITheme.INFO}]Output:[/{CLITheme.INFO}]")
            console.print(Panel(result.output, border_style=CLITheme.INFO, padding=(0, 1)))

        if result.error:
            console.print()
            console.print(f"  [{CLITheme.ERROR}]Error:[/{CLITheme.ERROR}]")
            console.print(Panel(result.error, border_style=CLITheme.ERROR, padding=(0, 1)))

        console.print()
        Prompt.ask("Press Enter to continue", default="")
        return True

    def run_all_automations(self):
        """Run all enabled automations."""
        self.clear_screen()
        self.show_header("Run All Enabled Automations")

        automations = self.registry.discover_automations()
        enabled = [a for a in automations if a.enabled]

        if not enabled:
            print_warning("No enabled automations found.")
            Prompt.ask("\nPress Enter to continue", default="")
            return True

        console.print(f"Found [{CLITheme.INFO}]{len(enabled)}[/{CLITheme.INFO}] enabled automation(s).")
        console.print()

        if not Confirm.ask("Do you want to run all enabled automations?"):
            return True

        console.print()
        console.print("Running automations...")
        console.print()

        results = self.scheduler.run_all_enabled(automations)

        # Show results table
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

        # Summary
        failed = sum(1 for r in results.values() if r.status.value == "failed")
        success = sum(1 for r in results.values() if r.status.value == "success")

        console.print()
        if failed > 0:
            print_error(f"{failed} automation(s) failed, {success} succeeded.")
        else:
            print_success(f"All {success} automation(s) completed successfully!")

        console.print()
        Prompt.ask("Press Enter to continue", default="")
        return True

    def view_schedules(self):
        """View upcoming scheduled executions."""
        self.clear_screen()
        self.show_header("Upcoming Scheduled Executions")

        automations = self.registry.discover_automations()
        upcoming = self.scheduler.get_upcoming_executions(automations)

        if not upcoming:
            print_info("No scheduled executions found.")
            print_info("Make sure automations have CRON schedules configured.")
            console.print()
            Prompt.ask("Press Enter to continue", default="")
            return True

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
        console.print()
        Prompt.ask("Press Enter to continue", default="")
        return True

    def register_automation_menu(self):
        """Interactive menu for registering a new automation."""
        self.clear_screen()
        self.show_header("Register New Automation")

        name = Prompt.ask("Enter automation name")
        if not name:
            print_error("Name is required.")
            Prompt.ask("\nPress Enter to continue", default="")
            return True

        description = Prompt.ask("Enter description (optional)", default="")
        cron = Prompt.ask("Enter CRON schedule (optional, e.g., '0 9 * * *')", default="")
        if not cron:
            cron = None

        script_type_choice = Prompt.ask(
            "Script type",
            choices=["python", "shell", "auto"],
            default="auto",
        )
        script_type = None if script_type_choice == "auto" else script_type_choice

        console.print()
        console.print("Registering automation...")
        console.print()

        try:
            automation_dir = self.automations_dir / name
            automation = self.registry.register_automation(
                automation_dir=automation_dir,
                name=name,
                description=description,
                cron_schedule=cron,
                script_type=script_type,
            )

            if automation.config.script_path:
                print_success(f"Found script: {automation.config.script_path.name}")
            else:
                print_warning("No script found. Please add run.py or run.sh to the automation directory.")

            console.print()
            print_success("Automation registered successfully!")

            console.print()
            console.print(
                Panel(
                    f"[{CLITheme.INFO}]To enable/disable or modify schedule, edit:[/{CLITheme.INFO}]\n"
                    f"[{CLITheme.HIGHLIGHT}]{automation_dir / 'config.yaml'}[/{CLITheme.HIGHLIGHT}]",
                    title="[bold]Next Steps[/bold]",
                    border_style=CLITheme.INFO,
                    padding=(1, 2),
                )
            )

        except Exception as e:
            print_error(f"Failed to register automation: {e}")

        console.print()
        Prompt.ask("Press Enter to continue", default="")
        return True

    def view_automation_details(self):
        """View detailed information about a specific automation."""
        self.clear_screen()
        self.show_header("Automation Details")

        automations = self.registry.discover_automations()

        if not automations:
            print_warning("No automations found.")
            Prompt.ask("\nPress Enter to continue", default="")
            return True

        # Create selection list
        choices = [f"{i+1}" for i in range(len(automations))]
        choices.append("b")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style=CLITheme.ACCENT, width=4)
        table.add_column(style=CLITheme.HIGHLIGHT)

        for i, automation in enumerate(automations):
            table.add_row(f"[{CLITheme.ACCENT}]{i+1}[/{CLITheme.ACCENT}]", automation.name)

        table.add_row(f"[{CLITheme.ACCENT}]b[/{CLITheme.ACCENT}]", "[dim]Back to main menu[/dim]")

        console.print(table)
        console.print()

        choice = Prompt.ask("Select automation", choices=choices, default="b")

        if choice == "b":
            return True

        try:
            index = int(choice) - 1
            if 0 <= index < len(automations):
                automation = automations[index]
                self.show_automation_details(automation)
        except (ValueError, IndexError):
            print_error("Invalid selection.")
            Prompt.ask("\nPress Enter to continue", default="")

        return True

    def show_automation_details(self, automation):
        """Show detailed information about an automation."""
        self.clear_screen()
        self.show_header(f"Details: {automation.name}")

        schedule = self.scheduler.get_effective_schedule(automation)
        status = AutomationStatus.ENABLED if automation.enabled else AutomationStatus.DISABLED
        status_color, status_icon = get_status_style(status)

        details_table = Table(show_header=False, box=None, padding=(0, 1))
        details_table.add_column(style=CLITheme.MUTED, width=20)
        details_table.add_column(style=CLITheme.HIGHLIGHT)

        details_table.add_row("Name:", automation.name)
        details_table.add_row("Status:", f"[{status_color}]{status_icon} {status.value.upper()}[/{status_color}]")
        details_table.add_row("Description:", automation.config.description or "No description")
        details_table.add_row("Schedule:", schedule or "global/default")
        details_table.add_row("Script Type:", str(automation.config.script_type) if automation.config.script_type else "auto-detected")
        details_table.add_row("Script Path:", str(automation.config.script_path) if automation.config.script_path else "Not found")
        details_table.add_row("Directory:", str(automation.path))

        console.print(details_table)
        console.print()
        Prompt.ask("Press Enter to continue", default="")
        return True

    def run(self):
        """Run the interactive CLI loop."""
        while True:
            try:
                should_continue = self.show_main_menu()
                if not should_continue:
                    break
            except KeyboardInterrupt:
                console.print()
                console.print()
                print_info("Exiting...")
                break
            except Exception as e:
                console.print()
                print_error(f"An error occurred: {e}")
                Prompt.ask("\nPress Enter to continue", default="")


@click.command()
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
def main(automations_dir: Path, config_dir: Path):
    """Interactive CLI menu for automation management."""
    cli = InteractiveCLI(automations_dir, config_dir)
    cli.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
