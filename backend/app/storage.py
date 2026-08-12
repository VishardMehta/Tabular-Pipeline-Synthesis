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

# profile_json added in stage 3. /generate has no ProfileCard of its own to
# work from - GenerateRequest is deliberately empty, see its docstring in
# models.py - so /profile has to leave the card here for /generate to read
# back. NULL until a profile has actually run for this dataset.
#
# Added with ALTER rather than folded into _SCHEMA's CREATE TABLE, because
# CREATE TABLE IF NOT EXISTS does nothing to a table that already exists from
# before this column was added. init_db() runs this on every boot, so a
# developer's existing local ./data/app.db picks the column up rather than
# erroring on every insert that no longer matches the old shape.
_ADD_PROFILE_COLUMN = "ALTER TABLE datasets ADD COLUMN profile_json TEXT"

# Whether the profile's problem_type was asserted by the caller rather than
# inferred. Added by ALTER for the identical reason as the column above.
#
# Recorded here rather than on ProfileCard deliberately. The card is serialised
# into the prompt, so a new field on it would change every prompt and
# invalidate the recorded cassettes - and provenance is a fact about the
# request, not about the dataset, so this row is where it belongs.
_ADD_TASK_OVERRIDDEN_COLUMN = (
    "ALTER TABLE datasets ADD COLUMN task_overridden INTEGER NOT NULL DEFAULT 0"
)

# One row per attempt, not per generation - a repaired second attempt is a
# second row, not an overwrite, so the failed first attempt stays on record
# for whatever eventually reads token and latency data out of this table.
_GENERATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS generations (
    id             TEXT PRIMARY KEY,
    dataset_id     TEXT NOT NULL,
    attempt        INTEGER NOT NULL,
    state          TEXT NOT NULL,
    provider       TEXT NOT NULL,
    model          TEXT NOT NULL,
    profile_json   TEXT NOT NULL,
    result_json    TEXT,
    input_tokens   INTEGER,
    output_tokens  INTEGER,
    latency_ms     INTEGER NOT NULL,
    error_code     TEXT,
    error_message  TEXT,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_generations_dataset_id ON generations (dataset_id);
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
        connection.executescript(_GENERATIONS_SCHEMA)
        with contextlib.suppress(sqlite3.OperationalError):
            connection.execute(_ADD_PROFILE_COLUMN)
        with contextlib.suppress(sqlite3.OperationalError):
            connection.execute(_ADD_TASK_OVERRIDDEN_COLUMN)


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


def save_profile(
    dataset_id: str, profile_json: str, task_was_overridden: bool = False
) -> None:
    """Persist a computed ProfileCard so /generate can read it back.

    Overwrites silently on a repeat call for the same dataset - profiling is
    deterministic (profiler.py fixes its RNG seed), so a second profile of
    the same target column reproduces the first exactly, and there is no
    older version worth keeping.

    Advances `state` in the same statement. That column was written once at
    insert and read by nothing, which made it dead data asserting a lifecycle
    the code never advanced. One dataset genuinely has two observable states
    here - uploaded, and profiled - so the column now records the one fact it
    is capable of recording, in the single place that fact changes.
    """
    with connect() as connection:
        connection.execute(
            "UPDATE datasets SET profile_json = ?, state = ?, task_overridden = ? "
            "WHERE id = ?",
            (profile_json, JobState.COMPLETE.value, int(task_was_overridden), dataset_id),
        )


def insert_generation(
    *,
    dataset_id: str,
    attempt: int,
    state: str,
    provider: str,
    model: str,
    profile_json: str,
    result_json: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    latency_ms: int,
    error_code: str | None,
    error_message: str | None,
) -> str:
    """Record one LLM call attempt. `state` is "success" or "failed" - not
    JobState, which describes the dataset's lifecycle, not one provider call."""
    generation_id = str(uuid.uuid4())
    with connect() as connection:
        connection.execute(
            "INSERT INTO generations (id, dataset_id, attempt, state, provider, model, "
            "profile_json, result_json, input_tokens, output_tokens, latency_ms, "
            "error_code, error_message, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                generation_id,
                dataset_id,
                attempt,
                state,
                provider,
                model,
                profile_json,
                result_json,
                input_tokens,
                output_tokens,
                latency_ms,
                error_code,
                error_message,
                datetime.now(UTC).isoformat(),
            ),
        )
    return generation_id


def get_generations(dataset_id: str) -> list[sqlite3.Row]:
    """Every recorded attempt for one dataset, oldest first. Not on the
    critical path of any route yet - stage 3 only needs writes - but reading
    the data back is what a later usage report and these tests are for."""
    with connect() as connection:
        cursor = connection.execute(
            "SELECT * FROM generations WHERE dataset_id = ? ORDER BY created_at", (dataset_id,)
        )
        return cursor.fetchall()


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
