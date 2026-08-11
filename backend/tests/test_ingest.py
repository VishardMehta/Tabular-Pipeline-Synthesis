"""Ingest, driven by the fixture corpus in tests/fixtures.

The fixtures were written before the implementation. Every rejection path has a
file behind it, so a test cannot pass by agreeing with a bug in the code it is
testing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import heuristics, ingest
from app.errors import AppError, ErrorCode

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str):
    return ingest.load_dataset(FIXTURES / name)


def code_for(name: str) -> ErrorCode:
    with pytest.raises(AppError) as raised:
        load(name)
    return raised.value.code


# --- Acceptance -------------------------------------------------------------


def test_good_file_loads():
    frame = load("good_small.csv")
    assert frame.shape == (5, 5)
    assert list(frame.columns) == ["id", "age", "city", "signup", "churn"]


def test_unicode_and_padded_headers_survive_verbatim():
    """Header text is data. Silently stripping or transliterating it would make
    the generated code reference a column name the file does not contain."""
    frame = load("messy_headers.csv")
    assert list(frame.columns) == [
        "Customer ID",
        "Total Spend (£)",
        "naïve_score",
        "  padded  ",
        "日付",
    ]


def test_column_count_exactly_at_the_limit_is_accepted():
    """MAX_COLS is a ceiling, not a fence. 1000 passes, 1001 does not."""
    frame = load("wide_1000_columns.csv")
    assert frame.shape[1] == heuristics.MAX_COLS


# --- Rejections -------------------------------------------------------------


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("empty.csv", ErrorCode.EMPTY_DATASET),
        ("header_only.csv", ErrorCode.HEADER_ONLY),
        ("single_column.csv", ErrorCode.SINGLE_COLUMN),
        ("duplicate_columns.csv", ErrorCode.DUPLICATE_COLUMNS),
        ("wide_1001_columns.csv", ErrorCode.TOO_MANY_COLUMNS),
        ("ragged_rows.csv", ErrorCode.UNPARSEABLE_CSV),
    ],
)
def test_each_bad_fixture_raises_its_own_code(fixture: str, expected: ErrorCode):
    assert code_for(fixture) is expected


def test_duplicate_columns_names_the_offenders():
    """The message has to name them, or the user cannot act on it."""
    with pytest.raises(AppError) as raised:
        load("duplicate_columns.csv")
    assert "id" in raised.value.message
    assert raised.value.details["columns"] == "id"


def test_duplicates_are_caught_before_pandas_mangles_them():
    """pandas resolves `id, id` to `id, id.1`. Code generated against `id.1`
    would reference a column the user's file does not have, so the check must
    run on the raw header."""
    with pytest.raises(AppError) as raised:
        load("duplicate_columns.csv")
    assert "id.1" not in raised.value.message


def test_single_column_is_reported_as_such_not_as_a_column_count_problem():
    with pytest.raises(AppError) as raised:
        load("single_column.csv")
    assert raised.value.code is ErrorCode.SINGLE_COLUMN
    assert "only_column" in raised.value.message


# --- Size limits ------------------------------------------------------------


def test_oversized_upload_is_refused_and_leaves_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(heuristics, "MAX_FILE_MB", 1)
    payload = b"a,b\n" + b"1,2\n" * 400_000  # comfortably over 1MB

    with pytest.raises(AppError) as raised:
        ingest.ingest(payload, upload_dir=tmp_path)

    assert raised.value.code is ErrorCode.FILE_TOO_LARGE
    assert list(tmp_path.iterdir()) == [], "partial upload was left on disk"


def test_memory_limit_rejects_a_frame_that_parsed_fine(tmp_path, monkeypatch):
    """The gap MAX_FILE_MB cannot see: small on disk, large once resident."""
    monkeypatch.setattr(heuristics, "MAX_MEMORY_MB", 0)
    with pytest.raises(AppError) as raised:
        ingest.ingest(b"a,b\n1,x\n2,y\n", upload_dir=tmp_path)
    assert raised.value.code is ErrorCode.DATASET_TOO_LARGE_IN_MEMORY


def test_rejected_upload_does_not_accumulate_files(tmp_path):
    """Every refusal path has to clean up, or the disk fills with rejects."""
    with pytest.raises(AppError):
        ingest.ingest(b"id,id\n1,2\n", upload_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_accepted_upload_is_stored_under_a_uuid_not_the_users_filename(tmp_path):
    """A filename is attacker controlled. It goes to the database as data and
    is never interpolated into a path."""
    path, _ = ingest.ingest(b"a,b\n1,2\n", upload_dir=tmp_path)
    assert path.parent == tmp_path
    assert path.suffix == ".csv"
    assert len(path.stem) == 36  # uuid4


# --- Stage 2 trap, guarded before it can be sprung --------------------------


# The cardinality-vs-sampling trap this file used to guard with an xfail is
# resolved architecturally, not just fixed: profiler.py never computes
# unique_count from anything but the full column, at any file size. See
# test_cardinality_is_never_computed_from_a_sample in test_profiler.py for the
# real assertion.
