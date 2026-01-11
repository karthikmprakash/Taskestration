"""Python script runner."""

import subprocess
import time
from pathlib import Path

from loguru import logger

from ..core.runner import AutomationRunner, RunnerResult, RunnerStatus


class PythonRunner(AutomationRunner):
    """Runner for Python scripts."""

    def can_run(self, script_path: Path) -> bool:
        """Check if this is a Python script."""
        return script_path.suffix.lower() == ".py" or script_path.name.startswith("run.py")

    def run(
        self,
        script_path: Path,
        working_directory: Path | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> RunnerResult:
        """Execute Python script."""
        start_time = time.time()
        logger.info(f"Executing Python script: {script_path}")

        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return RunnerResult(
                status=RunnerStatus.FAILED,
                error=f"Script not found: {script_path}",
                exit_code=1,
            )

        # Prepare environment
        import os

        env = os.environ.copy()

        # Add project root to PYTHONPATH so scripts can import from src.utils
        # Project root is the parent of the src directory
        project_root = Path(__file__).parent.parent.parent
        pythonpath = env.get("PYTHONPATH", "")
        if pythonpath:
            env["PYTHONPATH"] = f"{project_root}{os.pathsep}{pythonpath}"
        else:
            env["PYTHONPATH"] = str(project_root)

        if env_vars:
            env.update(env_vars)

        # Prepare working directory
        cwd = str(working_directory) if working_directory else None

        try:
            # Execute Python script
            result = subprocess.run(
                ["python3", str(script_path)],
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
        return "python"
