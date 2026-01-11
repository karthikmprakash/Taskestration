# Automation Control Panel

A scalable automation control panel that manages Python and shell script automations with CRON scheduling support. Built with SOLID principles for extensibility and maintainability.

## Architecture

The project follows a clean architecture with clear separation of concerns:

```
.
├── automations/              # Individual automation folders
│   ├── example_python/       # Example Python automation
│   └── example_shell/        # Example shell automation
├── config/                   # Global configuration
│   └── global.yaml          # Global CRON schedule and settings
├── scripts/                  # CLI control scripts
│   ├── register.py          # Register new automations
│   └── run.py               # Run automations
└── src/                      # Core framework
    ├── core/                 # Base abstractions
    │   ├── automation.py    # Automation models
    │   └── runner.py        # Runner interface
    ├── runners/             # Concrete runners
    │   ├── python_runner.py
    │   ├── shell_runner.py
    │   └── runner_factory.py
    ├── registry/            # Automation registry
    │   └── registry.py
    └── scheduler/           # CRON scheduler
        └── scheduler.py
```

## Features

- **Language Agnostic**: Supports both Python and shell scripts
- **CRON Scheduling**: Per-automation or global CRON schedules
- **Extensible**: Easy to add new script types via runner interface
- **Registration System**: Simple CLI to register new automations
- **SOLID Principles**: Clean, maintainable, and scalable architecture

## Installation

Install the package using `uv`:

```bash
# Install in editable mode
uv pip install -e .

# Or using uv sync (if using uv project)
uv sync
```

After installation, you can use the commands:

- `automation-register` - Register new automations
- `automation-run` - Run automations
- `automation-scheduler` - Scheduler daemon for automatic execution

Or run the scripts directly (if installed):

```bash
python -m scripts.register
python -m scripts.run
python -m scripts.scheduler
```

## Usage

After installation, you can use the commands in several ways:

### Register a New Automation

```bash
# Using entry point (recommended)
uv run automation-register my_automation --description "My automation" --cron "0 9 * * *"

# Or as Python module
python -m scripts.register my_automation --description "My automation" --cron "0 9 * * *"

# Register with script type hint
uv run automation-register my_automation --type python
```

### Run Automations

```bash
# List all automations
uv run automation-run

# Run a specific automation
uv run automation-run my_automation

# Run all enabled automations
uv run automation-run --all

# Run with verbose output
uv run automation-run my_automation --verbose

# Output as JSON
uv run automation-run my_automation --json

# List upcoming scheduled executions
uv run automation-run --schedule

# List next 5 upcoming executions
uv run automation-run --schedule --limit 5

# Output schedule as JSON
uv run automation-run --schedule --json
```

Or using Python modules:

```bash
python -m scripts.run
python -m scripts.run my_automation --verbose
python -m scripts.run --schedule
```

### Automatic Scheduling

The framework includes a scheduler daemon that automatically executes automations based on their CRON schedules:

```bash
# Run scheduler daemon (runs continuously)
uv run automation-scheduler

# Run scheduler once (for testing)
uv run automation-scheduler --once

# Custom check interval (default: 60 seconds)
uv run automation-scheduler --check-interval 30

# With custom log level
uv run automation-scheduler --log-level DEBUG
```

The scheduler daemon:

- Continuously monitors all enabled automations
- Checks for due automations every 60 seconds (configurable)
- Automatically executes automations when their CRON schedule matches
- Prevents duplicate executions (won't run the same automation twice within 60 seconds)
- Logs all executions and errors

### Viewing Upcoming Schedules

You can view all upcoming scheduled executions:

```bash
# List all upcoming scheduled executions
uv run automation-run --schedule

# Limit to next N executions
uv run automation-run --schedule --limit 5

# JSON output
uv run automation-run --schedule --json
```

Example output:

```
Upcoming scheduled executions:

  sort_screenshots: 2026-01-08 10:00:00 (in 42m 15s) [local]
    Schedule: 0 * * * *
  backup_data: 2026-01-08 12:00:00 (in 2h 42m 15s) [global]
    Schedule: 0 12 * * *
```

### Creating an Automation

1. **Create automation directory**:

```bash
mkdir -p automations/my_automation
```

2. **Add your script**:

   - Python: `automations/my_automation/run.py` or any `.py` file
   - Shell: `automations/my_automation/run.sh` or any `.sh`/`.bash` file

3. **Create config file** (`automations/my_automation/config.yaml`):

```yaml
name: my_automation
description: My automation description
enabled: true
cron_schedule: "0 9 * * *" # Optional: specific schedule
script_type: python # Optional: will be auto-detected
```

4. **Register** (optional, config will be auto-created if missing):

```bash
python scripts/register.py my_automation
```

### Global Configuration

Edit `config/global.yaml` to set global defaults:

```yaml
# Global CRON schedule (used by automations without their own schedule)
cron_schedule: "0 9 * * *" # Daily at 9 AM

# Enable/disable all automations
enabled: true
# Optional log directory
# log_directory: "./logs"
```

## Automation Structure

Each automation should be in its own folder with:

- `config.yaml` - Automation configuration
- `run.py` or `run.sh` - Executable script (or any matching pattern)

The framework will automatically detect:

- `run.py`, `main.py`, or any `.py` file for Python scripts
- `run.sh`, `run.bash`, or any `.sh`/`.bash` file for shell scripts

## Architecture Principles

### SOLID Principles Applied

1. **Single Responsibility**: Each module has one clear purpose

   - `AutomationRunner`: Execute scripts
   - `AutomationRegistry`: Manage automation discovery and registration
   - `AutomationScheduler`: Handle scheduling and execution control

2. **Open/Closed**: Easy to extend with new runner types

   - Implement `AutomationRunner` interface for new script types
   - Register via `RunnerFactory.register_runner()`

3. **Liskov Substitution**: All runners are interchangeable via interface

4. **Interface Segregation**: Clean `AutomationRunner` interface

5. **Dependency Inversion**: Depend on abstractions (`AutomationRunner`) not concretions

## Examples

See `automations/example_python/` and `automations/example_shell/` for example implementations.

## CRON Schedule Format

Standard CRON format:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

Examples:

- `"0 9 * * *"` - Daily at 9 AM
- `"0 */6 * * *"` - Every 6 hours
- `"0 0 * * 0"` - Weekly on Sunday at midnight
- `"*/30 * * * *"` - Every 30 minutes

## Development

### Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Or use make
make install-dev
```

### Code Quality

```bash
# Run all checks (recommended)
./run_checks.sh

# Or using make
make check

# Individual checks
make format    # Format code
make lint      # Check linting
make type-check # Type checking

# Or using uv directly
uv run ruff format .
uv run ruff check .
uv run mypy src scripts
```

### Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines on contributing to this project.

## License

MIT
