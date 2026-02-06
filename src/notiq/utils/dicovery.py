import os
from pathlib import Path


def autodiscover_tasks(base_dir: str | Path) -> list[str]:
    """
    Scans a directory for .py files and converts them to
    dotted module paths relative to the CWD.
    """
    target = Path(base_dir).resolve()
    modules = []

    if not target.exists():
        return []

    for full_path in target.rglob("*.py"):
        if full_path.name == "__init__.py":
            continue

        try:
            # Make path relative to where the user runs the command
            rel_path = full_path.relative_to(Path.cwd())
            # Convert to dotted notation
            module = str(rel_path.with_suffix("")).replace(os.sep, ".")
            modules.append(module)
        except ValueError:
            # This can happen if the path is not relative to CWD,
            # which is unlikely with resolved paths but handled for safety.
            continue
    return modules
