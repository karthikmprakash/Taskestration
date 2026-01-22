#!/usr/bin/env python3
"""Scheduler daemon for automatic automation execution."""

import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli import CLITheme, print_error, print_info, print_success, print_warning
from src.registry import AutomationRegistry
from src.runners import RunnerFactory
from src.scheduler import AutomationScheduler, GlobalConfig

console = Console()


class SchedulerDaemon:
    """Daemon that continuously checks and runs scheduled automations."""

    def __init__(
        self,
        automations_dir: Path,
        config_dir: Path,
        check_interval: int = 60,
    ):
        """
        Initialize scheduler daemon.

        Args:
            automations_dir: Directory containing automations
            config_dir: Directory containing global config
            check_interval: Interval in seconds to check for due automations
        """
        self.automations_dir = automations_dir
        self.config_dir = config_dir
        self.check_interval = check_interval
        self.running = False

        # Load configuration
        config_path = config_dir / "global.yaml"
        self.global_config = GlobalConfig.load(config_path)

        # Initialize components
        self.registry = AutomationRegistry(automations_dir)
        self.runner_factory = RunnerFactory()
        self.scheduler = AutomationScheduler(self.global_config, self.runner_factory)

        # Track last run times per automation to prevent duplicates
        self.last_runs: dict[str, datetime] = {}

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, _frame):
        """Handle shutdown signals."""
        console.print()
        print_info(f"Received signal {signum}, shutting down...")
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _should_execute(self, automation_name: str, _scheduled_time: datetime) -> bool:
        """
        Check if automation should execute (prevents duplicates).

        Args:
            automation_name: Name of automation
            scheduled_time: Scheduled execution time

        Returns:
            True if should execute
        """
        last_run = self.last_runs.get(automation_name)
        if last_run:
            # Only run if at least 1 minute has passed since last run
            # This prevents duplicate executions in the same minute
            time_diff = abs((datetime.now() - last_run).total_seconds())
            if time_diff < 60:
                return False

        # Update last run time
        self.last_runs[automation_name] = datetime.now()
        return True

    def _check_and_run(self):
        """Check for due automations and run them."""
        try:
            # Discover automations
            automations = self.registry.discover_automations()

            if not automations:
                return

            # Check for automations that are due
            now = datetime.now()
            results = self.scheduler.check_and_run_due(automations)

            for automation_name, result in results.items():
                # Get the automation to check schedule
                automation = next((a for a in automations if a.name == automation_name), None)

                if not automation:
                    continue

                # Verify it's actually time to run
                schedule = self.scheduler.get_effective_schedule(automation)
                if not schedule:
                    continue

                # Check if we should execute (prevent duplicates)
                next_run = self.scheduler.get_next_run_time(automation, now)
                if next_run and self._should_execute(automation_name, next_run):
                    if result.status.value == "success":
                        logger.info(f"✓ {automation_name}: executed successfully")
                    elif result.status.value == "failed":
                        logger.error(f"✗ {automation_name}: execution failed - {result.error}")
                    else:
                        logger.debug(f"⊘ {automation_name}: {result.status.value}")

        except Exception as e:
            logger.error(f"Error checking/running automations: {e}")

    def run(self):
        """Run the scheduler daemon."""
        console.print()
        console.print(
            Panel(
                f"[bold {CLITheme.ACCENT}]Automation Scheduler Daemon[/bold {CLITheme.ACCENT}]",
                border_style=CLITheme.ACCENT,
                padding=(1, 2),
            )
        )
        console.print()

        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column(style=CLITheme.MUTED, width=20)
        info_table.add_column(style=CLITheme.HIGHLIGHT)
        info_table.add_row("Status:", f"[{CLITheme.SUCCESS}]Starting...[/{CLITheme.SUCCESS}]")
        info_table.add_row("Check interval:", f"{self.check_interval} seconds")
        info_table.add_row("Automations dir:", str(self.automations_dir))
        console.print(info_table)
        console.print()

        logger.info("Starting scheduler daemon...")
        logger.info(f"Checking interval: {self.check_interval} seconds")
        logger.info(f"Automations directory: {self.automations_dir}")

        self.running = True

        # Initial check
        self._check_and_run()

        # Main loop
        while self.running:
            try:
                time.sleep(self.check_interval)
                if self.running:  # Check again after sleep
                    self._check_and_run()
            except KeyboardInterrupt:
                console.print()
                print_info("Received keyboard interrupt, shutting down...")
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                print_error(f"Error in scheduler loop: {e}")
                logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if there's an error
                time.sleep(self.check_interval)

        console.print()
        print_info("Scheduler daemon stopped.")
        logger.info("Scheduler daemon stopped.")

    def run_once(self):
        """Run once (for testing)."""
        console.print()
        console.print(
            Panel(
                f"[bold {CLITheme.ACCENT}]Running Scheduler Once[/bold {CLITheme.ACCENT}]",
                border_style=CLITheme.ACCENT,
                padding=(1, 2),
            )
        )
        console.print()
        logger.info("Running scheduler once...")
        self._check_and_run()
        console.print()
        print_success("Check complete.")
        logger.info("Check complete.")


@click.command()
@click.option(
    "--check-interval",
    type=int,
    default=60,
    help="Interval in seconds to check for due automations",
    show_default=True,
)
@click.option("--once", is_flag=True, help="Run once and exit (for testing)")
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
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Log level",
    show_default=True,
)
def main(
    check_interval: int,
    once: bool,
    automations_dir: Path,
    config_dir: Path,
    log_level: str,
):
    """Scheduler daemon for automatic automation execution."""
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
    )

    # Create and run daemon
    daemon = SchedulerDaemon(
        automations_dir=automations_dir,
        config_dir=config_dir,
        check_interval=check_interval,
    )

    if once:
        daemon.run_once()
    else:
        daemon.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
