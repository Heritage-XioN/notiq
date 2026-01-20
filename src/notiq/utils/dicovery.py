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

    # Requires Python 3.12+ for Path.walk()
    for root, dirs, files in target.walk():  # pyright: ignore[reportUnusedVariable, reportAttributeAccessIssue]
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = root / file
                try:
                    # Make path relative to where the user runs the command
                    rel_path = full_path.relative_to(Path.cwd())
                    # Convert to dotted notation
                    module = str(rel_path.with_suffix("")).replace(os.sep, ".")  # pyright: ignore[reportUnknownArgumentType]
                    modules.append(module)
                except ValueError:
                    continue
    return modules
