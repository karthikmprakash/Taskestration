"""CRON scheduler for managing automation execution."""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.automation import Automation
from ..core.runner import RunnerResult, RunnerStatus
from ..runners import RunnerFactory
from ..utils.logging import configure_logging


@dataclass
class GlobalConfig:
    """Global configuration for automation control panel."""

    cron_schedule: Optional[str] = None
    enabled: bool = True
    log_directory: Optional[Path] = None

    @classmethod
    def load(cls, config_path: Path) -> "GlobalConfig":
        """Load global config from file."""
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r") as f:
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

        data = {
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

    def should_run(self, automation: Automation) -> bool:
        """
        Check if automation should be run based on schedule.

        Args:
            automation: Automation to check

        Returns:
            True if automation should run
        """
        if not self.global_config.enabled:
            return False

        if not automation.enabled:
            return False

        return True

    def run_automation(
        self,
        automation: Automation,
        use_global_schedule: bool = False,
    ) -> RunnerResult:
        """
        Execute an automation.

        Args:
            automation: Automation to execute
            use_global_schedule: If True, use global schedule regardless of automation config

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

    def get_effective_schedule(self, automation: Automation) -> Optional[str]:
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
