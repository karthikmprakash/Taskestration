"""Automation registry for managing registered automations."""

from pathlib import Path

import yaml

from ..core.automation import Automation, AutomationConfig, ScriptType


class AutomationRegistry:
    """Registry for managing automations."""

    CONFIG_FILE = "config.yaml"
    SCRIPT_PATTERNS = {
        "python": ["run.py", "main.py", "*.py"],
        "shell": ["run.sh", "run.bash", "*.sh", "*.bash"],
    }

    def __init__(self, automations_dir: Path):
        """
        Initialize registry.

        Args:
            automations_dir: Directory containing automation folders
        """
        self.automations_dir = Path(automations_dir)
        self.automations_dir.mkdir(parents=True, exist_ok=True)

    def discover_automations(self) -> list[Automation]:
        """
        Discover all automations in the automations directory.

        Returns:
            List of discovered Automation objects
        """
        automations: list[Automation] = []

        if not self.automations_dir.exists():
            return automations

        for automation_dir in self.automations_dir.iterdir():
            if not automation_dir.is_dir():
                continue

            automation = self.load_automation(automation_dir)
            if automation:
                automations.append(automation)

        return automations

    def load_automation(self, automation_dir: Path) -> Automation | None:
        """
        Load automation from directory.

        Args:
            automation_dir: Directory containing automation

        Returns:
            Automation object or None if invalid
        """
        config_path = automation_dir / self.CONFIG_FILE

        if not config_path.exists():
            return None

        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                return None

            # Load base config
            script_type_str = config_data.get("script_type")
            script_type: ScriptType | None = None
            if script_type_str:
                try:
                    script_type = ScriptType(script_type_str)
                except ValueError:
                    script_type = None

            config = AutomationConfig(
                name=config_data.get("name", automation_dir.name),
                description=config_data.get("description", ""),
                cron_schedule=config_data.get("cron_schedule"),
                enabled=config_data.get("enabled", True),
                script_type=script_type,
                working_directory=automation_dir,
            )

            # Find script path
            script_path = self._find_script(automation_dir, config.script_type)
            if script_path:
                config.script_path = script_path
                if not config.script_type:
                    # Infer script type from extension
                    if script_path.suffix == ".py":
                        config.script_type = ScriptType.PYTHON
                    elif script_path.suffix in {".sh", ".bash", ".zsh"}:
                        config.script_type = ScriptType.SHELL

            return Automation(path=automation_dir, config=config)

        except Exception as e:
            print(f"Error loading automation from {automation_dir}: {e}")
            return None

    def _find_script(self, automation_dir: Path, script_type: ScriptType | None) -> Path | None:
        """Find script file in automation directory."""
        if script_type:
            patterns = self.SCRIPT_PATTERNS.get(script_type.value, [])
        else:
            # Try all patterns
            patterns = []
            for patterns_list in self.SCRIPT_PATTERNS.values():
                patterns.extend(patterns_list)

        # Common script names
        common_names = ["run.py", "run.sh", "run.bash", "main.py", "main.sh"]

        # Try common names first
        for name in common_names:
            script_path = automation_dir / name
            if script_path.exists():
                return script_path

        # Try patterns
        for pattern in patterns:
            for script_path in automation_dir.glob(pattern):
                if script_path.is_file():
                    return script_path

        return None

    def register_automation(
        self,
        automation_dir: Path,
        name: str,
        description: str = "",
        cron_schedule: str | None = None,
        script_type: str | None = None,
    ) -> Automation:
        """
        Register a new automation.

        Args:
            automation_dir: Directory for the automation
            name: Automation name
            description: Automation description
            cron_schedule: CRON schedule (optional)
            script_type: Script type hint (optional)

        Returns:
            Created Automation object
        """
        automation_dir = Path(automation_dir)
        automation_dir.mkdir(parents=True, exist_ok=True)

        config_path = automation_dir / self.CONFIG_FILE

        # Convert script_type string to enum
        script_type_enum: ScriptType | None = None
        if script_type:
            try:
                script_type_enum = ScriptType(script_type)
            except ValueError:
                script_type_enum = None

        # Find script if exists
        script_path = self._find_script(automation_dir, script_type_enum)

        config_data = {
            "name": name,
            "description": description,
            "enabled": True,
        }

        if cron_schedule:
            config_data["cron_schedule"] = cron_schedule

        if script_type:
            config_data["script_type"] = script_type

        if script_path:
            config_data["script_path"] = str(script_path.relative_to(automation_dir))

        # Write config
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        return self.load_automation(automation_dir) or Automation(
            path=automation_dir,
            config=AutomationConfig(
                name=name,
                description=description,
                cron_schedule=cron_schedule,
                working_directory=automation_dir,
                script_path=script_path,
                script_type=script_type_enum,
            ),
        )
