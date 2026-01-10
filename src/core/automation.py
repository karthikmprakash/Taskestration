"""Base automation class and configuration models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from enum import Enum

class ScriptType(str,Enum):
    PYTHON = "python"
    SHELL = "shell"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class AutomationConfig:
    """Configuration for an automation."""

    name: str
    description: str
    cron_schedule: Optional[str] = None  # CRON expression (e.g., "0 9 * * *")
    enabled: bool = True
    script_type: Optional[ScriptType] = None  # "python" or "shell"
    script_path: Optional[Path] = None
    working_directory: Optional[Path] = None

    def uses_global_schedule(self) -> bool:
        """Check if automation uses global CRON schedule."""
        return self.cron_schedule is None or self.cron_schedule == ""

    def get_schedule(self, global_cron: Optional[str]) -> Optional[str]:
        """Get effective CRON schedule (local or global)."""
        if self.uses_global_schedule():
            return global_cron
        return self.cron_schedule


@dataclass
class Automation:
    """Represents an automation with its configuration and path."""

    path: Path
    config: AutomationConfig

    @property
    def name(self) -> str:
        """Get automation name."""
        return self.config.name

    @property
    def enabled(self) -> bool:
        """Check if automation is enabled."""
        return self.config.enabled

if __name__ == "__main__":
    x = ScriptType.PYTHON
    print(x)
    print(ScriptType.SHELL)