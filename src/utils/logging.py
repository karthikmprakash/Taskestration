"""Logging utilities for automations using loguru."""

import functools
import sys
from collections.abc import Callable
from pathlib import Path

from loguru import logger

# Configure loguru to use a clean format for automation scripts
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Also add a file handler if log directory is configured
_log_dir: Path | None = None


def configure_logging(log_directory: Path | None = None) -> None:
    """Configure logging with optional file output."""
    global _log_dir
    _log_dir = log_directory

    if log_directory:
        log_directory.mkdir(parents=True, exist_ok=True)
        log_file = log_directory / "automations.log"
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
        )


def log_automation[F: Callable[..., int]](func: F) -> F:
    """
    Decorator to automatically add logging to automation main functions.

    Logs:
    - Function entry with parameters
    - Execution time
    - Success/failure status
    - Errors and exceptions

    Usage:
        @log_automation
        def main():
            # automation code
            return 0
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> int:
        func_name = func.__name__
        logger.info(f"Starting automation: {func_name}")

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Log result
            if result == 0:
                logger.success(f"Automation '{func_name}' completed successfully")
            else:
                logger.warning(f"Automation '{func_name}' completed with exit code {result}")

            return result

        except KeyboardInterrupt:
            logger.warning(f"Automation '{func_name}' interrupted by user")
            return 130  # Standard exit code for SIGINT

        except Exception as e:
            logger.exception(f"Automation '{func_name}' failed with error: {e}")
            return 1

    return wrapper  # type: ignore


def get_logger():
    """Get the configured logger instance."""
    return logger
