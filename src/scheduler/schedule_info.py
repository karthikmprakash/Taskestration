"""Schedule information models."""

from dataclasses import dataclass
from datetime import datetime

from ..core.automation import Automation


@dataclass
class ScheduledExecution:
    """Information about a scheduled automation execution."""

    automation: Automation
    next_run_time: datetime
    cron_schedule: str
    is_using_global: bool = False

    def __lt__(self, other: "ScheduledExecution") -> bool:
        """Compare by next run time for sorting."""
        return self.next_run_time < other.next_run_time

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ScheduledExecution({self.automation.name}, "
            f"next={self.next_run_time.isoformat()}, "
            f"schedule={self.cron_schedule})"
        )
