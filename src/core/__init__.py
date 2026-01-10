"""Core abstractions for the automation framework."""

from .automation import Automation, AutomationConfig
from .runner import AutomationRunner, RunnerResult

__all__ = ["Automation", "AutomationConfig", "AutomationRunner", "RunnerResult"]
