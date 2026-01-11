#!/usr/bin/env python3
"""Run automations."""

import argparse
import json
import sys
from pathlib import Path

from src.registry import AutomationRegistry
from src.runners import RunnerFactory
from src.scheduler import AutomationScheduler, GlobalConfig


def print_result(automation_name: str, result, verbose: bool = False):
    """Print execution result."""
    status_icons = {
        "success": "✓",
        "failed": "✗",
        "skipped": "⊘",
    }

    icon = status_icons.get(result.status.value, "?")
    print(f"{icon} {automation_name}: {result.status.value.upper()}")

    if verbose:
        if result.output:
            print(f"  Output:\n{result.output}")
        if result.error:
            print(f"  Error:\n{result.error}")
        if result.execution_time > 0:
            print(f"  Execution time: {result.execution_time:.2f}s")
        if result.exit_code != 0:
            print(f"  Exit code: {result.exit_code}")


def main():
    """Run automations."""
    parser = argparse.ArgumentParser(description="Run automations")
    parser.add_argument(
        "automation",
        nargs="?",
        help="Name of automation to run (omit to run all enabled)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all enabled automations",
    )
    parser.add_argument(
        "--use-global",
        action="store_true",
        help="Use global CRON schedule for all automations",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="List upcoming scheduled executions",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of upcoming executions to show (with --schedule)",
    )
    parser.add_argument(
        "--automations-dir",
        type=Path,
        default=Path(__file__).parent.parent / "automations",
        help="Directory containing automations (default: ./automations)",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path(__file__).parent.parent / "config",
        help="Directory containing global config (default: ./config)",
    )

    args = parser.parse_args()

    # Load global config
    config_path = args.config_dir / "global.yaml"
    global_config = GlobalConfig.load(config_path)

    # Initialize components
    registry = AutomationRegistry(args.automations_dir)
    runner_factory = RunnerFactory()
    scheduler = AutomationScheduler(global_config, runner_factory)

    # Discover automations
    automations = registry.discover_automations()

    if not automations:
        print("No automations found.")
        return 1

    # Handle schedule listing
    if args.schedule:
        from datetime import datetime

        upcoming = scheduler.get_upcoming_executions(automations, limit=args.limit)

        if not upcoming:
            print("No scheduled executions found.")
            print("Make sure automations have CRON schedules configured.")
            return 0

        if args.json:
            output = [
                {
                    "automation": exec.automation.name,
                    "next_run_time": exec.next_run_time.isoformat(),
                    "cron_schedule": exec.cron_schedule,
                    "is_using_global": exec.is_using_global,
                }
                for exec in upcoming
            ]
            print(json.dumps(output, indent=2))
        else:
            print("Upcoming scheduled executions:")
            print()
            now = datetime.now()
            for exec in upcoming:
                time_until = exec.next_run_time - now
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                seconds = int(time_until.total_seconds() % 60)

                if time_until.total_seconds() < 0:
                    time_str = "OVERDUE"
                elif hours > 0:
                    time_str = f"in {hours}h {minutes}m"
                elif minutes > 0:
                    time_str = f"in {minutes}m {seconds}s"
                else:
                    time_str = f"in {seconds}s"

                schedule_type = "global" if exec.is_using_global else "local"
                print(
                    f"  {exec.automation.name}: {exec.next_run_time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"({time_str}) [{schedule_type}]"
                )
                print(f"    Schedule: {exec.cron_schedule}")

        return 0

    results = {}

    if args.automation:
        # Run specific automation
        automation = next((a for a in automations if a.name == args.automation), None)

        if not automation:
            print(f"Automation '{args.automation}' not found.")
            print("\nAvailable automations:")
            for a in automations:
                print(f"  - {a.name}")
            return 1

        result = scheduler.run_automation(automation)
        results[automation.name] = result

        if not args.json:
            print_result(automation.name, result, args.verbose)
        else:
            print(
                json.dumps(
                    {
                        automation.name: {
                            "status": result.status.value,
                            "exit_code": result.exit_code,
                            "execution_time": result.execution_time,
                            "output": result.output,
                            "error": result.error,
                        }
                    },
                    indent=2,
                )
            )

    elif args.all:
        # Run all enabled automations
        results = scheduler.run_all_enabled(automations)

        if not args.json:
            for name, result in results.items():
                print_result(name, result, args.verbose)
        else:
            output_dict: dict[str, dict[str, object]] = {
                name: {
                    "status": result.status.value,
                    "exit_code": result.exit_code,
                    "execution_time": result.execution_time,
                    "output": result.output,
                    "error": result.error,
                }
                for name, result in results.items()
            }
            print(json.dumps(output_dict, indent=2))

    else:
        # List automations
        print("Available automations:")
        for automation in automations:
            status = "enabled" if automation.enabled else "disabled"
            schedule = scheduler.get_effective_schedule(automation)
            schedule_str = schedule if schedule else "global/default"
            print(f"  - {automation.name} ({status}, schedule: {schedule_str})")

    # Return exit code based on results
    if results:
        failed = any(r.status.value == "failed" for r in results.values())
        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
