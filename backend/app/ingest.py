"""Turning an uploaded file into a validated DataFrame, or a specific refusal.

Not prompt surface.

The ordering of the checks in this module is deliberate and load-bearing. Each
one assumes the previous ones have passed, and running them out of order
produces a technically true but useless error message. The sequence is:

  1. size, while streaming, before anything is buffered
  2. duplicate column names, read from the raw header before pandas sees it
  3. parse
  4. shape: empty, header-only, single column, column count
  5. resident memory

Duplicates are checked at step 2 rather than after parsing because pandas
silently mangles `id, id` into `id, id.1`. By the time a frame exists the
original names are gone, and any error raised afterwards would name a column
that does not appear in the user's file.
"""

from __future__ import annotations

import csv
import io
import uuid
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from app import heuristics
from app.config import settings
from app.errors import AppError, ErrorCode

# Read the upload in chunks so an oversized file is refused partway through
# rather than after the whole thing is resident. 1MB balances syscall count
# against how far past the limit we can overshoot before noticing.
CHUNK_BYTES = 1024 * 1024


def _mb(num_bytes: int) -> float:
    return num_bytes / (1024 * 1024)


def stream_to_disk(source: BinaryIO, upload_dir: Path) -> tuple[Path, int]:
    """Write an upload to a UUID-named path, refusing it if it exceeds the cap.

    The stored name is a fresh UUID and never the name the user supplied. The
    original filename goes to the database as data. It is never interpolated
    into a path, because a filename is attacker-controlled and path traversal
    is the entire reason that rule exists.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / f"{uuid.uuid4()}.csv"
    limit = heuristics.MAX_FILE_MB * 1024 * 1024
    written = 0

    try:
        with destination.open("wb") as handle:
            while chunk := source.read(CHUNK_BYTES):
                written += len(chunk)
                if written > limit:
                    raise AppError(
                        ErrorCode.FILE_TOO_LARGE,
                        f"This file is larger than the {heuristics.MAX_FILE_MB} MB limit. "
                        "Upload a smaller file, or a sample of this one.",
                        {"limit_mb": str(heuristics.MAX_FILE_MB)},
                    )
                handle.write(chunk)
    except AppError:
        destination.unlink(missing_ok=True)
        raise

    return destination, written


def reject_duplicate_columns(path: Path) -> None:
    """Read only the header row, and refuse repeated names.

    Runs before pandas because pandas resolves `id, id` to `id, id.1`, and code
    generated against `id.1` references a column the user's file does not have.
    """
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle), None)
    except UnicodeDecodeError as exc:
        raise AppError(
            ErrorCode.UNPARSEABLE_CSV,
            "This file is not valid UTF-8 text. Re-export it as UTF-8 CSV.",
        ) from exc

    if header is None:
        raise AppError(
            ErrorCode.EMPTY_DATASET,
            "This file is empty. Upload a CSV with a header row and at least one row.",
        )

    seen: set[str] = set()
    duplicates: list[str] = []
    for name in header:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)

    if duplicates:
        listed = ", ".join(duplicates)
        raise AppError(
            ErrorCode.DUPLICATE_COLUMNS,
            f"These column names appear more than once: {listed}. "
            "Every column needs a distinct name. Rename them and upload again.",
            {"columns": listed},
        )


def parse_csv(path: Path) -> pd.DataFrame:
    """Parse with the C engine.

    The engine is not negotiable and not a performance choice. The generated
    pipeline reads the same file with the C engine, so profiling it with a
    different one would mean the profile describes data the pipeline never sees.
    """
    try:
        return pd.read_csv(path, engine="c", encoding="utf-8-sig")
    except pd.errors.EmptyDataError as exc:
        raise AppError(
            ErrorCode.EMPTY_DATASET,
            "This file is empty. Upload a CSV with a header row and at least one row.",
        ) from exc
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        # The pandas message names the line and column, which is the most
        # actionable thing available, so it is passed through rather than
        # replaced with something friendlier and vaguer.
        raise AppError(
            ErrorCode.UNPARSEABLE_CSV,
            "This file could not be parsed as CSV. The parser reported: "
            f"{str(exc).splitlines()[0]}",
        ) from exc


def validate_shape(frame: pd.DataFrame) -> None:
    """Refuse frames that parsed cleanly but cannot be modelled."""
    n_rows, n_columns = frame.shape

    if n_columns == 0:
        raise AppError(
            ErrorCode.EMPTY_DATASET,
            "This file has no columns. Upload a CSV with a header row.",
        )

    if n_rows == 0:
        raise AppError(
            ErrorCode.HEADER_ONLY,
            "This file has a header row but no data. Upload a CSV with at least one row.",
        )

    # Checked before the column cap so a single-column file is told the useful
    # thing rather than being measured against a limit it is nowhere near.
    if n_columns == 1:
        raise AppError(
            ErrorCode.SINGLE_COLUMN,
            f"This file has only one column ({frame.columns[0]!r}). Modelling needs a "
            "target column and at least one feature to predict it from.",
            {"column": str(frame.columns[0])},
        )

    if n_columns > heuristics.MAX_COLS:
        raise AppError(
            ErrorCode.TOO_MANY_COLUMNS,
            f"This file has {n_columns} columns, above the {heuristics.MAX_COLS} limit. "
            "A file this wide is usually a feature matrix from another pipeline, or a "
            "transposed export.",
            {"n_columns": str(n_columns), "limit": str(heuristics.MAX_COLS)},
        )


def validate_memory(frame: pd.DataFrame) -> None:
    """Refuse a frame whose resident size would make profiling unsafe.

    Post-parse by necessity, so this protects the profiler rather than the
    parse. See the comment on MAX_MEMORY_MB.
    """
    resident = int(frame.memory_usage(deep=True).sum())
    limit = heuristics.MAX_MEMORY_MB * 1024 * 1024
    if resident > limit:
        raise AppError(
            ErrorCode.DATASET_TOO_LARGE_IN_MEMORY,
            f"This file is {_mb(resident):.0f} MB once loaded, above the "
            f"{heuristics.MAX_MEMORY_MB} MB working limit. Text columns expand "
            "considerably in memory, so a small file on disk can still be too large "
            "to profile. Upload a sample of it.",
            {"resident_mb": f"{_mb(resident):.0f}", "limit_mb": str(heuristics.MAX_MEMORY_MB)},
        )


def load_dataset(path: Path) -> pd.DataFrame:
    """Run every check in order and return the frame, or raise AppError."""
    reject_duplicate_columns(path)
    frame = parse_csv(path)
    validate_shape(frame)
    validate_memory(frame)
    return frame


def ingest(raw: bytes, upload_dir: Path | None = None) -> tuple[Path, pd.DataFrame]:
    """Store an upload and load it, cleaning up the file if any check refuses."""
    directory = upload_dir or Path(settings.upload_dir)
    path, _ = stream_to_disk(io.BytesIO(raw), directory)
    try:
        return path, load_dataset(path)
    except AppError:
        path.unlink(missing_ok=True)
        raise
