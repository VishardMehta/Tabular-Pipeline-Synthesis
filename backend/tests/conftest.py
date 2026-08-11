"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch) -> None:
    """Point the database and upload directory at a per-test temp directory.

    Autouse because a test that writes to the configured paths pollutes the
    developer's real ./data directory, and the failure that causes shows up
    later in an unrelated run.
    """
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A client with the lifespan actually run.

    TestClient only executes startup and shutdown inside a `with` block. Built
    without one, the database is never initialised and every route that touches
    it fails on a missing table.
    """
    with TestClient(create_app()) as test_client:
        yield test_client
