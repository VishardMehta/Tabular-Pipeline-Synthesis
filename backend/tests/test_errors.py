"""Integrity of the error table itself, before anything raises from it."""

from __future__ import annotations

from app.errors import ERROR_SPECS, AppError, ErrorCode


def test_every_code_has_a_spec():
    """A code without a spec would KeyError at the moment it is first raised."""
    assert set(ERROR_SPECS) == set(ErrorCode)


def test_no_orphan_specs():
    assert set(ERROR_SPECS) <= set(ErrorCode)


def test_statuses_are_client_or_server_errors():
    for code, spec in ERROR_SPECS.items():
        assert 400 <= spec.status < 600, code


def test_only_provider_failures_are_retryable():
    """Retryable means repeating the identical request may succeed.

    Every ingest rejection is a property of the file the user chose, so it
    reproduces exactly on a retry. Marking one of those retryable would put a
    button on screen that cannot work.

    VALIDATION_FAILED is deliberately absent: well formed output that failed a
    check needs repair, not a blind reroll against the same prompt.
    """
    expected = {
        ErrorCode.LLM_UNAVAILABLE,
        ErrorCode.LLM_RATE_LIMITED,
        ErrorCode.LLM_TIMEOUT,
        ErrorCode.LLM_INVALID_OUTPUT,
    }
    assert {code for code, spec in ERROR_SPECS.items() if spec.retryable} == expected


def test_to_response_carries_code_message_and_retryability():
    error = AppError(
        ErrorCode.DUPLICATE_COLUMNS,
        "Duplicate column names: id, id.",
        {"columns": "id"},
    )
    body = error.to_response()
    assert body.error.code == "DUPLICATE_COLUMNS"
    assert body.error.retryable is False
    assert body.error.details == {"columns": "id"}
    assert error.status_code == 422
