.PHONY: help lint format type-check test install-dev clean

help:
	@echo "Available commands:"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make test         - Run tests (if available)"
	@echo "  make clean        - Clean up cache files"

install-dev:
	uv pip install -e ".[dev]"

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy src scripts

check: lint type-check
	@echo "All checks passed!"

check-script:
	./run_checks.sh

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache dist build 2>/dev/null || true
