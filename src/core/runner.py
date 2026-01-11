"""Base runner interface for executing automations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RunnerStatus(Enum):
    """Status of automation execution."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RunnerResult:
    """Result of automation execution."""

    status: RunnerStatus
    output: str = ""
    error: str = ""
    exit_code: int = 0
    execution_time: float = 0.0

    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == RunnerStatus.SUCCESS


class AutomationRunner(ABC):
    """Abstract base class for automation runners."""

    @abstractmethod
    def can_run(self, script_path: Path) -> bool:
        """
        Check if this runner can execute the given script.

        Args:
            script_path: Path to the script file

        Returns:
            True if this runner can execute the script
        """
        pass

    @abstractmethod
    def run(
        self,
        script_path: Path,
        working_directory: Path | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> RunnerResult:
        """
        Execute the automation script.

        Args:
            script_path: Path to the script to execute
            working_directory: Working directory for execution
            env_vars: Environment variables to set

        Returns:
            RunnerResult with execution details
        """
        pass

    @abstractmethod
    def get_script_type(self) -> str:
        """Get the script type this runner handles (e.g., 'python', 'shell')."""
        pass
