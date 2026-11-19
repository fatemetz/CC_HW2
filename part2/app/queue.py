"""Queue stored as one name per line.

The HTTP server must call these functions. Tests call them directly,
with a temporary directory, and do not start Docker.
"""

from __future__ import annotations

from pathlib import Path


def join(path: str | Path, name: str) -> int:
    """Append one person and return the ticket number."""

    cleaned_name = name.strip()

    if (
        not cleaned_name
        or len(cleaned_name) > 40
        or "\n" in name
    ):
        raise ValueError("Invalid name")

    queue_path = Path(path)

    if queue_path.exists():
        names = queue_path.read_text(encoding="utf-8").splitlines()
    else:
        names = []

    names.append(cleaned_name)

    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        "\n".join(names) + "\n",
        encoding="utf-8",
    )

    return len(names)


def take(path: str | Path) -> str:
    """Remove and return the first name."""

    queue_path = Path(path)

    if not queue_path.exists():
        raise LookupError("Queue is empty")

    names = queue_path.read_text(encoding="utf-8").splitlines()

    if not names:
        raise LookupError("Queue is empty")

    first_name = names.pop(0)

    queue_path.write_text(
        "\n".join(names) + ("\n" if names else ""),
        encoding="utf-8",
    )

    return first_name