# Contributing to Notiq

First off, thank you for considering contributing to Notiq! It's people like you that make Notiq such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [iheritage934@gmail.com](mailto:iheritage934@gmail.com).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title** for the issue
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** to demonstrate the steps
- **Describe the behavior you observed** and explain why it's a problem
- **Explain the expected behavior** you expected to see
- **Include your environment details**: Python version, OS, Redis version, etc.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful** to most users
- **List any alternatives** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `master`
2. **Set up your development environment** (see below)
3. **Make your changes** following our coding standards
4. **Add tests** if applicable
5. **Ensure all tests pass**
6. **Update documentation** if needed
7. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Redis and rabbitmq(optional) servers
- Git

### Setting Up the Development Environment

```bash
# Clone your fork
git clone https://github.com/Heritage-XioN/notiq.git
cd notiq

# Install dependencies with uv (recommended)
uv sync --all-groups

# Or with pip
pip install -e ".[dev]"

# Set up pre-commit hooks
uv run pre-commit install
```

### Environment Configuration

Create a `.env` file in the project root:

```env
NOTIQ_BROKER_URL=redis://localhost:6379/0
NOTIQ_RESULT_BACKEND=redis://localhost:6379/0
NOTIQ_TASK_DIR=./tasks
```

## Coding Standards

### Code Style

We use the following tools to maintain code quality:

- **[Ruff](https://docs.astral.sh/ruff/)** - Linting and formatting
- **[Mypy](https://mypy.readthedocs.io/)** - Type checking
- **[Pyright](https://microsoft.github.io/pyright/)** - Static type analysis

Run all checks before submitting:

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check .

# Type checking
uv run mypy src/


# or just run the pre-commit manually,
# this runs the above checks
uv run pre-commit run --all-files
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(scheduler): add cron expression support
fix(worker): resolve connection timeout issue
docs(readme): update installation instructions
```

### Type Hints

- Always use type hints for function parameters and return values
- Use `from __future__ import annotations` for modern annotations
- Prefer specific types over `Any` when possible

```python
def process_task(task_id: int, data: dict[str, Any]) -> TaskResult:
    ...
```

### Documentation

- Write docstrings for all public functions, classes, and modules
- Follow the Google docstring style
- Include type information in docstrings when helpful

```python
def schedule_task(
    task: Callable[..., Any],
    name: str,
    interval_seconds: int,
) -> str:
    """
    Schedule a task to run at regular intervals.

    Args:
        task: The callable to schedule.
        name: A unique identifier for this scheduled task.
        interval_seconds: How often to run the task, in seconds.

    Returns:
        The unique task ID for the scheduled task.

    Raises:
        ValueError: If interval_seconds is less than 1.
    """
    ...
```

## Pull Request Process

1. **Create a feature branch** from `master`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** and commit following our commit message guidelines

3. **Push to your fork**:
   ```bash
   git push origin feat/your-feature-name
   ```

4. **Open a Pull Request** against the `master` branch

5. **Fill out the PR template** with:
   - Description of changes
   - Related issue numbers
   - Screenshots (if applicable)
   - Testing performed

6. **Wait for review** - maintainers will review your PR and may request changes

7. **Address feedback** and push additional commits as needed

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
