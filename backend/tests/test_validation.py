"""Validator tests, driven by the fixture corpus in
tests/fixtures/validation_corpus.py.

The corpus was written before validation.py, one entry per check, each
changing exactly one thing away from a baseline that passes everything.
These assert structure only: which check_id passed or failed, never exact
message prose - the same rule CLAUDE.md states for the profiler and the
prompt applies here too.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app import llm, profiler, storage, validation
from app.models import ValidationSeverity
from tests.cassette_provider import CassetteProvider
from tests.fixtures.validation_corpus import BASE_PROFILE, CORPUS, GOOD_RESULT

FIXTURES = Path(__file__).parent / "fixtures" / "profiler"


@pytest.fixture(autouse=True)
def _init_storage():
    """llm.generate() (used by the cassette-backed tests below) writes to
    the generations table on every attempt - see the identical fixture in
    test_llm.py for why this has to run init_db() itself."""
    storage.init_db()

_FAIL_CHECK_IDS = {
    "syntax_compile",
    "ast_import_allowlist",
    "dangerous_calls",
    "hallucinated_columns",
    "target_column_referenced",
    "gen_result_self_consistency",
}
_WARN_CHECK_IDS = {
    "pipeline_or_column_transformer",
    "random_state_set",
    "split_or_cross_validation",
    "primary_metric_computed",
    "declared_columns_exist",
    # Not in the stage's enumerated WARN list - see the comment on
    # _check_dropped_columns_not_referenced in app/validation.py for why it
    # was added anyway.
    "dropped_columns_not_referenced",
}


def test_the_baseline_passes_every_check():
    """If this fails, a corpus entry's "only one check fails" premise is
    unverifiable - every other entry is a diff against this one."""
    report = validation.validate(GOOD_RESULT, BASE_PROFILE)
    failed = [c.check_id for c in report.checks if not c.passed]
    assert failed == []
    assert report.passed is True
    assert report.error_count == 0
    assert report.warning_count == 0


def test_every_check_id_is_in_the_enumerated_fail_or_warn_list():
    report = validation.validate(GOOD_RESULT, BASE_PROFILE)
    seen = {c.check_id for c in report.checks}
    assert seen <= _FAIL_CHECK_IDS | _WARN_CHECK_IDS
    for check in report.checks:
        if check.check_id in _FAIL_CHECK_IDS:
            assert check.severity is ValidationSeverity.ERROR
        else:
            assert check.severity is ValidationSeverity.WARNING


@pytest.mark.parametrize("entry", CORPUS, ids=[entry.name for entry in CORPUS])
def test_corpus_entry_fails_exactly_the_expected_checks(entry):
    report = validation.validate(entry.result, BASE_PROFILE)
    seen_ids = {c.check_id for c in report.checks}

    # Every expected failure must actually be a check that ran - a check
    # skipped because syntax failed can never be the thing a fixture proves.
    assert entry.expect_failing <= seen_ids, (
        f"{entry.name}: expected checks {entry.expect_failing - seen_ids} did not run "
        f"(only {seen_ids} did)"
    )

    for check in report.checks:
        expected_pass = check.check_id not in entry.expect_failing
        assert check.passed is expected_pass, (
            f"{entry.name}: {check.check_id} passed={check.passed}, expected {expected_pass}\n"
            f"message: {check.message}"
        )


def test_report_counts_are_consistent_across_the_whole_corpus():
    """The same invariant test_api.py checks against the placeholder report,
    now checked against every real corpus entry."""
    for entry in CORPUS:
        report = validation.validate(entry.result, BASE_PROFILE)
        failed = [c for c in report.checks if not c.passed]
        assert report.error_count == sum(
            1 for c in failed if c.severity is ValidationSeverity.ERROR
        )
        assert report.warning_count == sum(
            1 for c in failed if c.severity is ValidationSeverity.WARNING
        )
        assert report.passed is (report.error_count == 0)


def test_syntax_failure_omits_every_ast_dependent_check():
    """Never assert a property that was not tested: with no parseable AST,
    the checks that need one must be absent, not fabricated as passing."""
    entry = next(e for e in CORPUS if e.name == "syntax_error")
    report = validation.validate(entry.result, BASE_PROFILE)
    seen_ids = {c.check_id for c in report.checks}
    assert seen_ids == {
        "syntax_compile",
        "gen_result_self_consistency",
        "declared_columns_exist",
    }


# --- Against the three real cassette generations from stage 3 ----------------


@pytest.fixture(
    params=["leaking_feature.csv", "skewed_regression.csv", "high_cardinality_categorical.csv"]
)
def cassette_profile_and_result(request):
    frame = pd.read_csv(FIXTURES / request.param, engine="c")
    profile = profiler.profile(frame, f"cassette-{request.param}", request.param, "target")
    result = llm.generate(profile, f"cassette-{request.param}", CassetteProvider())
    return profile, result


def test_real_generations_pass_validation(cassette_profile_and_result):
    """The three cassettes recorded in stage 3 are real Gemini output, not
    fixtures written to pass. If any check fires here it is a genuine
    finding about the model's output, not a bug in the corpus - reported
    separately rather than asserted away."""
    profile, result = cassette_profile_and_result
    report = validation.validate(result, profile)
    failed = [(c.check_id, c.message) for c in report.checks if not c.passed]
    assert failed == [], f"real generation failed validation: {failed}"
