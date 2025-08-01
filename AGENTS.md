# Contribution Guidelines

Welcome! This document describes how to contribute to this project and the standards to follow.

## Code Style
- Follow [PEP8](https://peps.python.org/pep-0008/) for Python, using **four spaces** for indentation.
- Keep lines under **120 characters** for readability.
- Every **public function and module** must have a clear, concise docstring that explains what it does.

## Commit Messages
- Use **short, imperative statements** for commit messages (e.g., "Add feature", "Fix bug", "Refactor module").
- Write in the present tense, as if you’re giving a command.

## Testing Before Commit
- Always run a syntax check before committing:
  ```bash
  python -m py_compile $(git ls-files '*.py')
If you add a new dependency, update requirements.txt immediately.

Pre-commit Linting
Before each commit, run lint checks:

bash
Copiar
Editar
pre-commit run --files $(git diff --name-only)
Make sure requirements.txt is up-to-date with any new dependencies.

Pull Requests (PRs)
Each PR description must include:

## Summary: What this change does.

## Testing: How you tested it and what the results were.

PRs should be focused and address a single logical change whenever possible.

General Guidance
Write self-documenting code and clear comments when logic is non-obvious.

Avoid unnecessary code duplication.

Prefer clarity and maintainability over cleverness.

Thanks for contributing!