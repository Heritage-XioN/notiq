"""
Validation utilities for monitoring components.

Provides sanitization and validation functions to prevent:
- Path traversal attacks in log file names
- Unbounded Prometheus label cardinality from invalid metric names
"""

import re
from pathlib import Path

# Regex for valid Prometheus metric/label names
# Must start with [a-zA-Z_], contain only [a-zA-Z0-9_], max 64 chars
VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


def validate_metric_name(name: str) -> str:
    """
    Validate and return a safe metric name for Prometheus labels.

    Prevents unbounded label cardinality by enforcing Prometheus naming
    conventions. This should be called at decoration time to fail fast.

    Args:
        name: The metric name to validate.

    Returns:
        The validated metric name (unchanged if valid).

    Raises:
        ValueError: If the name doesn't match Prometheus naming conventions.
    """
    if not isinstance(name, str) or not VALID_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid metric_name '{name}'. "
            "Must be 1-64 characters, start with [a-zA-Z_], "
            "and contain only [a-zA-Z0-9_]."
        )
    return name


def sanitize_log_filename(name: str) -> str:
    """
    Sanitize a name for use as a log filename.

    Prevents path traversal attacks by:
    - Stripping any directory components (e.g., "../" or absolute paths)
    - Replacing unsafe characters with underscores
    - Ensuring non-empty result

    Args:
        name: The raw name to sanitize.

    Returns:
        A safe filename string suitable for use in log file paths.
    """
    # Strip directory components to prevent path traversal
    safe = Path(name).name

    # Replace any characters that aren't alphanumeric, underscore, hyphen, or dot
    safe = re.sub(r"[^\w\-.]", "_", safe)

    # Ensure non-empty result
    return safe if safe else "default"
