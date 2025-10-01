# Repository Guidelines

## Project Structure & Module Organization
The repo currently contains `main.py` (entrypoint) and `pyproject.toml`. Keep reusable code inside a `damsan_api/` package so modules stay importable and cohesive. Place integration utilities or scripts under `tools/`, and keep configuration or seed data in `config/` or `data/` to avoid cluttering the root. Add README stubs in new directories so their intent stays obvious.

## Build, Test, and Development Commands
Create a Python 3.13 virtual environment before installing dependencies: `python3.13 -m venv .venv && source .venv/bin/activate`. Install the project in editable mode for local iteration: `pip install -e .[dev]` (define `[project.optional-dependencies.dev]` inside `pyproject.toml`). Run the executable entrypoint with `python -m main`. When workflows expand, capture them in `make` or `just` recipes so teammates can reuse single-command automation.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and describe module intent in a top-level docstring. Modules, packages, and functions stay snake_case (for example `damsan_api/user_service.py`), classes use PascalCase, and constants are UPPER_SNAKE. Prefer explicit type hints on public functions and avoid side effects at import time. Configure `ruff` (`ruff check`) and `black` (`black .`) via `pyproject.toml` to keep formatting consistent across the team.

## Testing Guidelines
Adopt pytest and mirror the source tree when naming tests (`tests/user/test_profile.py`). Test functions should read `test_<behavior>` and isolate external systems behind fixtures or fakes. Run `pytest --maxfail=1 --disable-warnings` locally, and add `pytest --cov=damsan_api` for coverage, targeting 80% line coverage or higher. Document shared fixtures in `tests/README.md` when introducing them.

## Commit & Pull Request Guidelines
Use Conventional Commits (`feat: add profile endpoint`) to clarify intent and enable automated release notes. Keep commits focused, and describe follow-up work in the body if needed. Pull requests should link to relevant issues, summarize scope, note risks, and list the commands you ran (for example `pytest`). Attach screenshots or sample payloads when adjusting API contracts, and request a second reviewer for changes that touch shared interfaces.
