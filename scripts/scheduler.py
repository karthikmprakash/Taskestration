#!/usr/bin/env python3
"""Scheduler daemon for automatic automation execution."""

import argparse
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.registry import AutomationRegistry
from src.runners import RunnerFactory
from src.scheduler import AutomationScheduler, GlobalConfig


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

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _should_execute(self, automation_name: str, scheduled_time: datetime) -> bool:
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
                automation = next(
                    (a for a in automations if a.name == automation_name), None
                )

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
                        logger.error(
                            f"✗ {automation_name}: execution failed - {result.error}"
                        )
                    else:
                        logger.debug(f"⊘ {automation_name}: {result.status.value}")

        except Exception as e:
            logger.error(f"Error checking/running automations: {e}")

    def run(self):
        """Run the scheduler daemon."""
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
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if there's an error
                time.sleep(self.check_interval)

        logger.info("Scheduler daemon stopped.")

    def run_once(self):
        """Run once (for testing)."""
        logger.info("Running scheduler once...")
        self._check_and_run()
        logger.info("Check complete.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scheduler daemon for automatic automation execution"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=60,
        help="Interval in seconds to check for due automations (default: 60)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)",
    )
    parser.add_argument(
        "--automations-dir",
        type=Path,
        default=Path(__file__).parent.parent / "automations",
        help="Directory containing automations (default: ./automations)",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path(__file__).parent.parent / "config",
        help="Directory containing global config (default: ./config)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=args.log_level,
    )

    # Create and run daemon
    daemon = SchedulerDaemon(
        automations_dir=args.automations_dir,
        config_dir=args.config_dir,
        check_interval=args.check_interval,
    )

    if args.once:
        daemon.run_once()
    else:
        daemon.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())

