#!/usr/bin/env python3
"""Register a new automation."""

import argparse
from pathlib import Path

from src.registry import AutomationRegistry


def main():
    """Register a new automation."""
    parser = argparse.ArgumentParser(description="Register a new automation")
    parser.add_argument(
        "name",
        help="Name of the automation (will be used as folder name)",
    )
    parser.add_argument(
        "-d",
        "--description",
        default="",
        help="Description of the automation",
    )
    parser.add_argument(
        "-c",
        "--cron",
        help="CRON schedule expression (e.g., '0 9 * * *' for daily at 9 AM)",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["python", "shell"],
        help="Script type (will be auto-detected if script exists)",
    )
    parser.add_argument(
        "--automations-dir",
        type=Path,
        default=Path(__file__).parent.parent / "automations",
        help="Directory containing automations (default: ./automations)",
    )

    args = parser.parse_args()

    registry = AutomationRegistry(args.automations_dir)
    automation_dir = args.automations_dir / args.name

    print(f"Registering automation: {args.name}")
    print(f"Directory: {automation_dir}")

    automation = registry.register_automation(
        automation_dir=automation_dir,
        name=args.name,
        description=args.description,
        cron_schedule=args.cron,
        script_type=args.type,
    )

    if automation.config.script_path:
        print(f"✓ Found script: {automation.config.script_path}")
    else:
        print("⚠ No script found. Please add run.py or run.sh to the automation directory.")

    print("✓ Automation registered successfully!")
    print("\nTo enable/disable or modify schedule, edit:")
    print(f"  {automation_dir / 'config.yaml'}")


if __name__ == "__main__":
    main()
