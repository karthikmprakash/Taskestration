"""Factory for creating appropriate automation runners."""

from pathlib import Path

from ..core.runner import AutomationRunner
from .python_runner import PythonRunner
from .shell_runner import ShellRunner


class RunnerFactory:
    """Factory to get appropriate runner for a script."""

    def __init__(self):
        """Initialize factory with available runners."""
        self._runners: list[AutomationRunner] = [
            PythonRunner(),
            ShellRunner(),
        ]

    def get_runner(self, script_path: Path) -> AutomationRunner | None:
        """
        Get appropriate runner for the given script path.

        Args:
            script_path: Path to the script

        Returns:
            Appropriate AutomationRunner or None if no runner matches
        """
        for runner in self._runners:
            if runner.can_run(script_path):
                return runner
        return None

    def register_runner(self, runner: AutomationRunner) -> None:
        """
        Register a new runner (for extensibility).

        Args:
            runner: Runner to register
        """
        self._runners.append(runner)
