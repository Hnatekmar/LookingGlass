# Contributing to LookingGlass

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 20+ (for Tampermonkey extension)

### Setup

```bash
git clone https://github.com/Hnatekmar/LookingGlass.git
cd LookingGlass
cp .env.example .env
# Edit .env with your model endpoints

# Python dependencies
uv sync --dev

# Extension dependencies (optional)
cd tampermonkey-extension && npm install && cd ..
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_something.py

# Run with timeout (tests should complete within 30s)
uv run pytest tests/ -v --timeout=30
```

Tests are located in the `tests/` directory. We use `pytest` with `pytest-asyncio`
for async tests and `pytest-timeout` to prevent hung tests.

## Code Style

- Python: PEP 8 with type hints for all function signatures
- Imports: standard library → third-party → local (separated by blank lines)
- TypeScript: Standard TS with strict mode
- Configuration: All env vars must be defined in `Settings` class in `config.py`
  and documented in `.env.example`

## Pull Request Process

1. Create a branch from `main` with a descriptive name:
   - `feat/` for new features
   - `fix/` for bug fixes
   - `chore/` for maintenance
   - `docs/` for documentation

2. Make your changes and ensure tests pass:
   ```bash
   uv run pytest
   ```

3. Update `.env.example` if you add new environment variables

4. Update docs if you change behavior or add features

5. Open a PR against `main` with a clear description of changes

## Adding a New OCR Provider

Currently, the OCR pipeline in `image_processing.py` routes between GLM-OCR SDK
and a generic VLM fallback via an `ENABLE_GLM_OCR` boolean. To add a new provider:

1. Add config fields to `app/config.py::Settings`
2. Add the provider client in a new file (e.g., `app/providers/`)
3. Add routing logic in `_extract_labels_from_image()` in `image_processing.py`
4. Add env vars to `.env.example`
5. Write tests
6. Update docs

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `chore:` — maintenance, deps, config
- `docs:` — documentation
- `refactor:` — code restructuring
- `test:` — adding or fixing tests

## Versioning

Version bumps are automatic via the `semantic-versioning.yml` workflow on pushes
to `main`. Commit messages determine the bump type:

- `BREAKING CHANGE` or `!:` → major bump
- `feat:` → minor bump
- `fix:` / `docs:` / `chore:` → patch bump

## Questions?

Open an issue or tag @zelvinator in a PR/issue comment.
