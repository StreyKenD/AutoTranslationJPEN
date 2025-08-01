# Contribution Guidelines

## Code Style
- Follow PEP8 with four-space indentation.
- Keep lines under 120 characters when possible.
- Provide docstrings for all public functions and modules.

## Commit Messages
- Use short, imperative messages ("Add feature", "Fix bug").

## Testing
- Before committing, run a syntax check:
  ```bash
  python -m py_compile $(git ls-files '*.py')
  ```
- Update `requirements.txt` if you add new dependencies.

## Pre-commit
Run lint checks before committing:
```bash
pre-commit run --files $(git diff --name-only)
```
Update `requirements.txt` if you add new dependencies.

## Pull Request
- The PR description must contain `## Summary` and `## Testing` sections describing the change and test results.
