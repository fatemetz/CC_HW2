
"""Queue stored as one name per line.

The HTTP server must call these functions. Tests call them directly,
with a temporary directory, and do not start Docker.
"""

from __future__ import annotations

import fcntl
import os
import tempfile
from pathlib import Path


def _write_names(queue_path: Path, names: list[str]) -> None:
    """Atomically replace the queue file."""

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=queue_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(
                "\n".join(names) + ("\n" if names else "")
            )
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, queue_path)

    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


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
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = queue_path.parent / "queue.lock"

    with lock_path.open("a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        if queue_path.exists():
            names = queue_path.read_text(
                encoding="utf-8"
            ).splitlines()
        else:
            names = []

        names.append(cleaned_name)
        _write_names(queue_path, names)

        return len(names)


def take(path: str | Path) -> str:
    """Remove and return the first name."""

    queue_path = Path(path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = queue_path.parent / "queue.lock"

    with lock_path.open("a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        if not queue_path.exists():
            raise LookupError("Queue is empty")

        names = queue_path.read_text(
            encoding="utf-8"
        ).splitlines()

        if not names:
            raise LookupError("Queue is empty")

        first_name = names.pop(0)
        _write_names(queue_path, names)

        return first_name
