"""Shell script runner."""

import subprocess
import time
from pathlib import Path

from loguru import logger

from ..core.runner import AutomationRunner, RunnerResult, RunnerStatus


class ShellRunner(AutomationRunner):
    """Runner for shell scripts."""

    def can_run(self, script_path: Path) -> bool:
        """Check if this is a shell script."""
        shell_extensions = {".sh", ".bash", ".zsh"}
        return script_path.suffix.lower() in shell_extensions or script_path.name.startswith(
            "run.sh"
        )

    def run(
        self,
        script_path: Path,
        working_directory: Path | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> RunnerResult:
        """Execute shell script."""
        start_time = time.time()
        logger.info(f"Executing shell script: {script_path}")

        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error=f"Script not found: {script_path}",
                exit_code=1,
            )

        # Check if script is executable
        if not script_path.is_file():
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error=f"Not a file: {script_path}",
                exit_code=1,
            )

        # Prepare environment
        env = None
        if env_vars:
            import os

            env = os.environ.copy()
            env.update(env_vars)

        # Prepare working directory
        cwd = str(working_directory) if working_directory else None

        try:
            # Determine shell based on script extension or default to bash
            shell = "bash"
            if script_path.suffix == ".zsh":
                shell = "zsh"
            elif script_path.suffix == ".sh":
                shell = "bash"

            # Execute shell script
            result = subprocess.run(
                [shell, str(script_path)],
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                timeout=3600,  # 1 hour timeout
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                logger.success(f"Script completed successfully in {execution_time:.2f}s")
                if result.stdout:
                    logger.debug(f"Script output:\n{result.stdout}")
                return RunnerResult(
                    status=RunnerStatus.SUCCESS,
                    output=result.stdout,
                    exit_code=0,
                    execution_time=execution_time,
                )
            else:
                logger.error(
                    f"Script failed with exit code {result.returncode} after {execution_time:.2f}s"
                )
                if result.stderr:
                    logger.error(f"Script error:\n{result.stderr}")
                if result.stdout:
                    logger.debug(f"Script output:\n{result.stdout}")
                return RunnerResult(
                    status=RunnerStatus.FAILED,
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode,
                    execution_time=execution_time,
                )
        except subprocess.TimeoutExpired:
            logger.error("Script execution timed out after 1 hour")
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error="Script execution timed out after 1 hour",
                exit_code=124,
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            logger.exception(f"Execution error: {e}")
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=time.time() - start_time,
            )

    def get_script_type(self) -> str:
        """Get script type."""
        return "shell"
