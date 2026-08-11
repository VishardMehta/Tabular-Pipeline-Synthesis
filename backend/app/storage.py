"""SQLite persistence and the TTL sweeper.

Not prompt surface.

Plain sqlite3 rather than an ORM, per the dependency list. One table, four
queries, no relationships worth mapping.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config import settings
from app.models import DatasetUploadResponse, JobState

# One hour between sweeps. The TTL is measured in hours, so sweeping more often
# buys nothing, and a dataset living up to an hour past its expiry is harmless
# when the guarantee is "deleted within a day", not "deleted to the second".
SWEEP_INTERVAL_S = 3600

_SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id           TEXT PRIMARY KEY,
    filename     TEXT NOT NULL,
    stored_path  TEXT NOT NULL,
    n_rows       INTEGER NOT NULL,
    n_columns    INTEGER NOT NULL,
    columns_json TEXT NOT NULL,
    state        TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets (created_at);
"""


def _db_path() -> Path:
    return Path(settings.db_path)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection with WAL on.

    WAL matters here because the TTL sweeper writes on a timer while requests
    are reading. Under the default rollback journal a sweep blocks readers for
    its duration; under WAL they proceed against the last committed snapshot.
    The pragma is per-database and persists, but setting it on every connection
    costs nothing and removes the ordering dependency on who connected first.
    """
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(_SCHEMA)


def insert_dataset(
    filename: str,
    stored_path: Path,
    n_rows: int,
    n_columns: int,
    columns: list[str],
) -> DatasetUploadResponse:
    """Record an ingested dataset and return the upload response for it."""
    dataset_id = str(uuid.uuid4())
    with connect() as connection:
        connection.execute(
            "INSERT INTO datasets (id, filename, stored_path, n_rows, n_columns, "
            "columns_json, state, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                dataset_id,
                filename,
                str(stored_path),
                n_rows,
                n_columns,
                json.dumps(columns),
                JobState.PENDING.value,
                datetime.now(UTC).isoformat(),
            ),
        )
    return DatasetUploadResponse(
        dataset_id=dataset_id,
        filename=filename,
        n_rows=n_rows,
        n_columns=n_columns,
        columns=columns,
        state=JobState.PENDING,
    )


def get_dataset(dataset_id: str) -> sqlite3.Row | None:
    with connect() as connection:
        cursor = connection.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        return cursor.fetchone()


def sweep_expired() -> int:
    """Delete expired rows and their files. Returns how many rows went.

    The file is removed before the row, so a crash between the two leaves an
    unreferenced row rather than a row pointing at a missing file. Both are
    recoverable, but a dangling row fails loudly on the next read while a
    missing file fails at profiling time, further from the cause.
    """
    cutoff = (datetime.now(UTC) - timedelta(hours=settings.dataset_ttl_hours)).isoformat()
    with connect() as connection:
        rows = connection.execute(
            "SELECT id, stored_path FROM datasets WHERE created_at < ?", (cutoff,)
        ).fetchall()
        for row in rows:
            Path(row["stored_path"]).unlink(missing_ok=True)
        connection.execute("DELETE FROM datasets WHERE created_at < ?", (cutoff,))
    return len(rows)


def sweep_orphan_files() -> int:
    """Delete upload files that no row references. Returns how many went.

    Ingest writes the file and then inserts the row, so anything that kills the
    process between the two leaves a file nothing points at. A sweeper that
    iterates rows can never reclaim those, and they accumulate silently until
    the disk fills. This was not theoretical: the first run of the API test
    suite produced one, when the insert failed on a missing table after the
    write had already succeeded.

    Only files older than the TTL are considered, so an upload being written
    right now is never mistaken for an orphan.
    """
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.is_dir():
        return 0

    with connect() as connection:
        referenced = {
            Path(row["stored_path"]).resolve()
            for row in connection.execute("SELECT stored_path FROM datasets")
        }

    cutoff = (datetime.now(UTC) - timedelta(hours=settings.dataset_ttl_hours)).timestamp()
    removed = 0
    for path in upload_dir.glob("*.csv"):
        if path.resolve() in referenced or path.stat().st_mtime >= cutoff:
            continue
        path.unlink(missing_ok=True)
        removed += 1
    return removed


async def sweep_forever() -> None:
    """Sweep on a timer for the life of the process.

    asyncio rather than a scheduler dependency. The try/except is what keeps it
    alive: an unhandled exception in a bare task kills the loop silently, and a
    TTL sweeper that stopped an hour after boot looks exactly like one that is
    working until the disk fills.
    """
    while True:
        await asyncio.sleep(SWEEP_INTERVAL_S)
        with contextlib.suppress(Exception):
            await asyncio.to_thread(sweep_expired)
            await asyncio.to_thread(sweep_orphan_files)
