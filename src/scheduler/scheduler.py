"""CRON scheduler for managing automation execution."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml
from croniter import croniter

from ..core.automation import Automation
from ..core.runner import RunnerResult, RunnerStatus
from ..runners import RunnerFactory
from ..utils.logging import configure_logging
from .schedule_info import ScheduledExecution


@dataclass
class GlobalConfig:
    """Global configuration for automation control panel."""

    cron_schedule: str | None = None
    enabled: bool = True
    log_directory: Path | None = None

    @classmethod
    def load(cls, config_path: Path) -> "GlobalConfig":
        """Load global config from file."""
        if not config_path.exists():
            return cls()

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            log_dir = None
            if data.get("log_directory"):
                log_dir = Path(data["log_directory"])

            return cls(
                cron_schedule=data.get("cron_schedule"),
                enabled=data.get("enabled", True),
                log_directory=log_dir,
            )
        except Exception:
            return cls()

    def save(self, config_path: Path) -> None:
        """Save global config to file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, bool | str] = {
            "enabled": self.enabled,
        }

        if self.cron_schedule:
            data["cron_schedule"] = self.cron_schedule

        if self.log_directory:
            data["log_directory"] = str(self.log_directory)

        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class AutomationScheduler:
    """Scheduler for executing automations."""

    def __init__(self, global_config: GlobalConfig, runner_factory: RunnerFactory):
        """
        Initialize scheduler.

        Args:
            global_config: Global configuration
            runner_factory: Factory for creating runners
        """
        self.global_config = global_config
        self.runner_factory = runner_factory

        # Configure logging if log directory is specified
        if global_config.log_directory:
            configure_logging(global_config.log_directory)

    def should_run(self, automation: Automation, check_time: datetime | None = None) -> bool:
        """
        Check if automation should be run based on schedule and time.

        Args:
            automation: Automation to check
            check_time: Time to check against (defaults to now)

        Returns:
            True if automation should run
        """
        if not self.global_config.enabled:
            return False

        if not automation.enabled:
            return False

        # Get effective schedule
        schedule = self.get_effective_schedule(automation)
        if not schedule:
            # No schedule means manual execution only
            return False

        # If check_time is provided, verify if it matches the schedule
        if check_time:
            try:
                cron = croniter(schedule, check_time)
                # Get the previous scheduled time
                prev_time = cron.get_prev(datetime)
                # Check if we're within a small window of the scheduled time
                time_diff = abs((check_time - prev_time).total_seconds())
                # Allow 60 second window for execution
                if time_diff > 60:
                    return False
            except Exception:
                # If CRON parsing fails, allow execution
                pass

        return True

    def run_automation(
        self,
        automation: Automation,
    ) -> RunnerResult:
        """
        Execute an automation.

        Args:
            automation: Automation to execute

        Returns:
            RunnerResult with execution details
        """
        if not self.should_run(automation):
            return RunnerResult(
                status=RunnerStatus.SKIPPED,
                output="Automation is disabled",
            )

        if not automation.config.script_path or not automation.config.script_path.exists():
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error=f"Script not found: {automation.config.script_path}",
                exit_code=1,
            )

        # Get appropriate runner
        runner = self.runner_factory.get_runner(automation.config.script_path)
        if not runner:
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error=f"No runner found for script: {automation.config.script_path}",
                exit_code=1,
            )

        # Execute
        working_dir = automation.config.working_directory or automation.path

        result = runner.run(
            script_path=automation.config.script_path,
            working_directory=working_dir,
        )

        return result

    def get_effective_schedule(self, automation: Automation) -> str | None:
        """
        Get effective CRON schedule for automation.

        Args:
            automation: Automation to get schedule for

        Returns:
            CRON schedule string or None
        """
        if automation.config.uses_global_schedule():
            return self.global_config.cron_schedule
        return automation.config.cron_schedule

    def get_next_run_time(
        self, automation: Automation, from_time: datetime | None = None
    ) -> datetime | None:
        """
        Calculate next run time for an automation.

        Args:
            automation: Automation to calculate next run for
            from_time: Starting time (defaults to now)

        Returns:
            Next run time or None if no schedule
        """
        schedule = self.get_effective_schedule(automation)
        if not schedule:
            return None

        try:
            from_time = from_time or datetime.now()
            cron = croniter(schedule, from_time)
            return cron.get_next(datetime)  # type: ignore[no-any-return]
        except Exception:
            return None

    def get_upcoming_executions(
        self,
        automations: list[Automation],
        limit: int | None = None,
        from_time: datetime | None = None,
    ) -> list[ScheduledExecution]:
        """
        Get all upcoming scheduled executions.

        Args:
            automations: List of automations to check
            limit: Maximum number of executions to return (None for all)
            from_time: Starting time (defaults to now)

        Returns:
            List of ScheduledExecution objects, sorted by next run time
        """
        from_time = from_time or datetime.now()
        upcoming = []

        for automation in automations:
            # Skip disabled automations
            if not automation.enabled or not self.global_config.enabled:
                continue

            schedule = self.get_effective_schedule(automation)
            if not schedule:
                continue

            next_run = self.get_next_run_time(automation, from_time)
            if next_run:
                is_global = automation.config.uses_global_schedule()
                upcoming.append(
                    ScheduledExecution(
                        automation=automation,
                        next_run_time=next_run,
                        cron_schedule=schedule,
                        is_using_global=is_global,
                    )
                )

        # Sort by next run time
        upcoming.sort()

        # Apply limit if specified
        if limit:
            upcoming = upcoming[:limit]

        return upcoming

    def check_and_run_due(
        self, automations: list[Automation], time_window: int = 60
    ) -> dict[str, RunnerResult]:
        """
        Check for automations that are due and run them.

        Args:
            automations: List of automations to check
            time_window: Time window in seconds to consider automations as due

        Returns:
            Dictionary mapping automation names to their results
        """
        results = {}
        now = datetime.now()

        for automation in automations:
            # Skip disabled automations
            if not automation.enabled or not self.global_config.enabled:
                continue

            # Get schedule
            schedule = self.get_effective_schedule(automation)
            if not schedule:
                continue

            # Check if it's time to run
            try:
                cron = croniter(schedule, now)
                prev_time = cron.get_prev(datetime)
                time_diff = abs((now - prev_time).total_seconds())

                # Check if we're within the time window
                if time_diff <= time_window and self.should_run(automation, now):
                    results[automation.name] = self.run_automation(automation)
            except Exception:
                # If CRON parsing fails, skip
                continue

        return results

    def run_all_enabled(self, automations: list[Automation]) -> dict[str, RunnerResult]:
        """
        Run all enabled automations.

        Args:
            automations: List of automations to run

        Returns:
            Dictionary mapping automation names to their results
        """
        results = {}

        for automation in automations:
            if self.should_run(automation):
                results[automation.name] = self.run_automation(automation)

        return results
