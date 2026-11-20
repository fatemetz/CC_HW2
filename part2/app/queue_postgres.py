"""Queue implementation backed by PostgreSQL."""

from __future__ import annotations

import psycopg


def initialize(dsn: str) -> None:
    """Create the queue tables and the shared lock row."""

    with psycopg.connect(dsn) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS queue_lock (
                id INTEGER PRIMARY KEY CHECK (id = 1)
            )
            """
        )

        connection.execute(
            """
            INSERT INTO queue_lock (id)
            VALUES (1)
            ON CONFLICT (id) DO NOTHING
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS queue_entries (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(40) NOT NULL
            )
            """
        )


def join(dsn: str, name: str) -> int:
    """Add one person and return the queue length after insertion."""

    cleaned_name = name.strip()

    if not cleaned_name or len(cleaned_name) > 40 or "\n" in name:
        raise ValueError("Invalid name")

    with psycopg.connect(dsn) as connection, connection.transaction():
        connection.execute(
            "SELECT id FROM queue_lock WHERE id = 1 FOR UPDATE"
        )

        connection.execute(
            "INSERT INTO queue_entries (name) VALUES (%s)",
            (cleaned_name,),
        )

        result = connection.execute(
            "SELECT COUNT(*) FROM queue_entries"
        ).fetchone()

        return int(result[0])


def take(dsn: str) -> str:
    """Remove and return the first person in the queue."""

    with psycopg.connect(dsn) as connection, connection.transaction():
        connection.execute(
            "SELECT id FROM queue_lock WHERE id = 1 FOR UPDATE"
        )

        row = connection.execute(
            """
                SELECT id, name
                FROM queue_entries
                ORDER BY id
                LIMIT 1
                """
        ).fetchone()

        if row is None:
            raise LookupError("Queue is empty")

        connection.execute(
            "DELETE FROM queue_entries WHERE id = %s",
            (row[0],),
        )

        return str(row[1])