# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-01-11

- Added `CHANGELOG.md` to track releases
-

## [0.1.0] - 2026-01-08

### Fixed

- Fixed linting errors (unused arguments, nested if statements)
- Fixed type checking errors in registry and scheduler modules
- Converted ScriptType string literals to enum values for type safety
- Fixed type annotations in automation registry
- Fixed variable name conflicts in run script
- Removed unused `use_global_schedule` parameter from `run_automation()` method

### Changed

- Updated logging decorator to use PEP 695 type parameters instead of TypeVar
- Improved type safety across the codebase

## [0.0.1] - Initial Release

### Added

- Core automation framework with Python and shell script support
- CRON scheduling system (per-automation and global schedules)
- Automation registry system
- CLI tools for registering and running automations
- Scheduler daemon for automatic execution
- Logging utilities with loguru integration
