"""The LLM layer: provider error mapping, the retry-with-repair loop, and
cassette-backed checks against real recorded generations.

Cassette tests assert structure only, never prose - CLAUDE.md's testing rule
applies here exactly as it does to the profiler and the prompt. What survives
here is: the response validates, the field order Gemini sent matches
GenResult's declaration order, every column the code references is a real
one, the primary metric matches what the profile already decided, and the
candidate list is bounded. None of that is about what the model said, only
about the shape it said it in.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pandas as pd
import pytest
from google.genai import errors as genai_errors
from pydantic import ValidationError

from app import llm, profiler, storage
from app.config import settings
from app.errors import AppError, ErrorCode
from app.llm import GeminiProvider, RawGeneration, StubProvider
from app.models import GenResult
from app.validation import referenced_column_literals
from tests.cassette_provider import CassetteProvider

FIXTURES = Path(__file__).parent / "fixtures" / "profiler"

CASSETTE_FIXTURES = [
    "leaking_feature.csv",
    "skewed_regression.csv",
    "high_cardinality_categorical.csv",
]


@pytest.fixture(autouse=True)
def _init_storage():
    """generate() writes to the generations table on every attempt. The
    isolated_storage fixture in conftest.py points settings.db_path at a
    fresh tmp_path, but nothing except the FastAPI lifespan normally calls
    init_db() to create the table there - these tests bypass the app
    entirely, so they have to call it themselves."""
    storage.init_db()


@pytest.fixture(params=CASSETTE_FIXTURES)
def cassette_profile(request):
    """A ProfileCard built the identical way record_cassettes.py built it.

    profiler.profile is deterministic (fixed RNG seed), so re-running it here
    reproduces the exact prompt that was hashed to name the cassette file.
    """
    frame = pd.read_csv(FIXTURES / request.param, engine="c")
    return profiler.profile(frame, f"cassette-{request.param}", request.param, "target")


# --- Cassette-backed structural invariants ------------------------------------


def test_cassette_generation_validates(cassette_profile):
    result = llm.generate(cassette_profile, "ds-cassette", CassetteProvider())
    assert isinstance(result, GenResult)


def test_field_order_preserved_on_the_wire(cassette_profile):
    from app import prompts

    provider = CassetteProvider()
    raw = provider.generate(
        system_prompt=prompts.SYSTEM_PROMPT,
        user_message=prompts.build_user_message(cassette_profile),
    )
    assert list(json.loads(raw.text).keys()) == list(GenResult.model_fields.keys())


def test_primary_metric_matches_the_profile(cassette_profile):
    result = llm.generate(cassette_profile, "ds-cassette", CassetteProvider())
    assert result.primary_metric == cassette_profile.primary_metric
    assert result.problem_type == cassette_profile.problem_type
    assert result.target_column == cassette_profile.target_column


def test_candidate_models_bounded(cassette_profile):
    result = llm.generate(cassette_profile, "ds-cassette", CassetteProvider())
    assert 2 <= len(result.candidate_models) <= 4


# The real implementation now lives in app/validation.py (stage 4), which
# needs the identical extraction for its own hallucinated-columns check.
# Reusing it here rather than keeping a second copy is exactly the point -
# see the module docstring there.
def _referenced_column_literals(code: str) -> set[str]:
    return referenced_column_literals(ast.parse(code))


def test_only_real_columns_referenced(cassette_profile):
    result = llm.generate(cassette_profile, "ds-cassette", CassetteProvider())
    known = {column.name for column in cassette_profile.columns}
    referenced = _referenced_column_literals(result.code)
    assert referenced <= known, f"referenced names not in the profile: {referenced - known}"


# --- GeminiProvider's own error mapping: no network -------------------------
#
# The cassette tests above exercise llm.generate()'s retry loop against
# StubProvider and CassetteProvider, neither of which ever raises a
# google-genai exception - GeminiProvider is the only implementation that
# does, so its 429/503/timeout branches need their own coverage rather than
# being taken on faith from the one live run reported alongside this stage.


def _provider() -> GeminiProvider:
    """Single-key provider: these tests are about error mapping, not rotation.

    One key keeps each case a straight assertion that a given google-genai
    exception becomes a given ErrorCode. With several keys a 429 would fail
    over and the test would be asserting rotation instead.
    """
    return GeminiProvider(api_keys=["test-key"], model=settings.llm_model, timeout_s=1)


def _provider_client(provider: GeminiProvider):
    """The cached genai.Client the provider will use for its only key."""
    return llm._KEY_RING.client(provider._api_keys[0])


def test_gemini_provider_maps_429_to_rate_limited():
    provider = _provider()
    error = genai_errors.ClientError(
        429, {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}
    )
    with (
        patch.object(_provider_client(provider).models, "generate_content", side_effect=error),
        pytest.raises(AppError) as exc_info,
    ):
        provider.generate(system_prompt="s", user_message="u")
    assert exc_info.value.code is ErrorCode.LLM_RATE_LIMITED


def test_gemini_provider_maps_503_to_unavailable():
    """503 was one call in ten in the stage 0 spike - routine, not exceptional."""
    provider = _provider()
    error = genai_errors.ServerError(503, {"message": "backend overloaded"})
    with (
        patch.object(_provider_client(provider).models, "generate_content", side_effect=error),
        pytest.raises(AppError) as exc_info,
    ):
        provider.generate(system_prompt="s", user_message="u")
    assert exc_info.value.code is ErrorCode.LLM_UNAVAILABLE


def test_gemini_provider_maps_other_client_errors_to_unavailable():
    """A 400 or 403 has no dedicated code in the frozen errors.py. Documented
    in llm.py as the closest existing meaning, not a perfect one."""
    provider = _provider()
    error = genai_errors.ClientError(403, {"message": "permission denied"})
    with (
        patch.object(_provider_client(provider).models, "generate_content", side_effect=error),
        pytest.raises(AppError) as exc_info,
    ):
        provider.generate(system_prompt="s", user_message="u")
    assert exc_info.value.code is ErrorCode.LLM_UNAVAILABLE


def test_gemini_provider_maps_504_server_error_to_timeout():
    """Measured live, not assumed: against this API, a deadline set via
    HttpOptions.timeout that is actually hit comes back as a 504
    DEADLINE_EXCEEDED ServerError, not as an httpx.TimeoutException. See the
    comment on this branch in llm.py."""
    provider = _provider()
    error = genai_errors.ServerError(
        504,
        {
            "message": "Deadline expired before operation could complete.",
            "status": "DEADLINE_EXCEEDED",
        },
    )
    with (
        patch.object(_provider_client(provider).models, "generate_content", side_effect=error),
        pytest.raises(AppError) as exc_info,
    ):
        provider.generate(system_prompt="s", user_message="u")
    assert exc_info.value.code is ErrorCode.LLM_TIMEOUT


def test_gemini_provider_maps_httpx_timeout_too():
    """The rarer path: the connection itself hangs rather than the server
    returning a deadline-exceeded response."""
    provider = _provider()
    with (
        patch.object(
            _provider_client(provider).models,
            "generate_content",
            side_effect=httpx.ReadTimeout("timed out"),
        ),
        pytest.raises(AppError) as exc_info,
    ):
        provider.generate(system_prompt="s", user_message="u")
    assert exc_info.value.code is ErrorCode.LLM_TIMEOUT


def test_default_provider_refuses_a_missing_key(monkeypatch):
    # Every slot must be cleared: one populated numbered key is still a
    # usable deployment, so blanking only GOOGLE_API_KEY proves nothing.
    for field in ("google_api_key", "google_api_key1", "google_api_key2", "google_api_key3"):
        monkeypatch.setattr(llm.settings, field, "")
    with pytest.raises(AppError) as exc_info:
        llm.default_provider()
    assert exc_info.value.code is ErrorCode.LLM_UNAVAILABLE


# --- Retry-with-repair, error mapping: no network, no cassette ---------------


def _valid_gen_result_json(profile) -> str:
    """A minimal but genuinely valid GenResult for whatever `profile` is
    given, so these tests do not hardcode values that drift if the fixture
    CSVs ever change."""
    return GenResult(
        problem_type=profile.problem_type,
        target_column=profile.target_column,
        primary_metric=profile.primary_metric,
        dropped_columns=[],
        preprocessing=[],
        candidate_models=[
            {"name": "LogisticRegression", "library": "scikit-learn", "rationale": "Baseline."},
            {
                "name": "HistGradientBoostingClassifier",
                "library": "scikit-learn",
                "rationale": "Stronger default.",
            },
        ],
        validation_strategy="Five-fold cross-validation.",
        analysis_summary="A minimal valid result for testing.",
        risks=["This is test output, not a real strategy."],
        code="import pandas as pd\ndf = pd.read_csv('data.csv', engine='c')\n",
    ).model_dump_json()


class _ScriptedProvider:
    """Returns a scripted sequence of raw texts, one per call. Raises if
    asked for more calls than were scripted."""

    name = "scripted"
    model = "scripted-model"

    def __init__(self, texts: list[str]) -> None:
        self._texts = list(texts)
        self.calls = 0

    def generate(self, *, system_prompt: str, user_message: str) -> RawGeneration:
        self.calls += 1
        text = self._texts.pop(0)
        return RawGeneration(text=text, input_tokens=7, output_tokens=11)


@pytest.fixture
def profile(cassette_profile):
    return cassette_profile


def test_invalid_output_is_repaired_on_the_second_attempt(profile):
    good = _valid_gen_result_json(profile)
    provider = _ScriptedProvider(texts=["not json at all", good])

    result = llm.generate(profile, "ds-repair", provider)

    assert provider.calls == 2
    assert result.target_column == profile.target_column
    rows = storage.get_generations("ds-repair")
    assert [row["state"] for row in rows] == ["failed", "success"]
    assert rows[0]["error_code"] == ErrorCode.LLM_INVALID_OUTPUT.value
    assert rows[1]["result_json"] is not None


def test_two_invalid_outputs_give_up_with_llm_invalid_output(profile):
    provider = _ScriptedProvider(texts=["not json", "still not json"])

    with pytest.raises(AppError) as exc_info:
        llm.generate(profile, "ds-repair-fail", provider)

    assert exc_info.value.code is ErrorCode.LLM_INVALID_OUTPUT
    assert provider.calls == 2
    rows = storage.get_generations("ds-repair-fail")
    assert len(rows) == 2
    assert all(row["state"] == "failed" for row in rows)


def test_repair_attempt_carries_the_validation_error_forward(profile):
    """The second attempt's prompt must actually change, or "repair" is just
    a second identical roll of the dice."""
    good = _valid_gen_result_json(profile)
    provider = _ScriptedProvider(texts=["{not: valid json", good])
    seen_messages: list[str] = []

    original_generate = provider.generate

    def spy(*, system_prompt: str, user_message: str) -> RawGeneration:
        seen_messages.append(user_message)
        return original_generate(system_prompt=system_prompt, user_message=user_message)

    provider.generate = spy  # type: ignore[method-assign]
    llm.generate(profile, "ds-repair-note", provider)

    assert len(seen_messages) == 2
    assert seen_messages[0] != seen_messages[1]
    assert "did not validate" in seen_messages[1]


def test_provider_failure_is_logged_and_reraised_without_retry(profile):
    provider = StubProvider()
    provider.error = AppError(ErrorCode.LLM_RATE_LIMITED, "slow down")

    with pytest.raises(AppError) as exc_info:
        llm.generate(profile, "ds-rate-limited", provider)

    assert exc_info.value.code is ErrorCode.LLM_RATE_LIMITED
    assert provider.calls == 1, "a provider-level failure is not the retry-with-repair case"
    rows = storage.get_generations("ds-rate-limited")
    assert len(rows) == 1
    assert rows[0]["error_code"] == ErrorCode.LLM_RATE_LIMITED.value


def test_successful_generation_is_logged_with_tokens_and_latency(profile):
    provider = StubProvider()
    provider.text = _valid_gen_result_json(profile)

    llm.generate(profile, "ds-success", provider)

    rows = storage.get_generations("ds-success")
    assert len(rows) == 1
    row = rows[0]
    assert row["state"] == "success"
    assert row["provider"] == "stub"
    assert row["input_tokens"] == 1
    assert row["output_tokens"] == 1
    assert row["latency_ms"] >= 0
    assert row["error_code"] is None
    assert json.loads(row["result_json"])["target_column"] == profile.target_column


def _schema_violating_json(profile) -> str:
    """Well-formed JSON that fails the schema (one candidate model, below
    min_length=2) rather than failing to parse at all. The more likely real
    failure - a live run has never produced unparseable text, only schema
    violations - so the repair path has to handle this case, not only a
    JSONDecodeError."""
    return json.dumps(
        {
            "problem_type": profile.problem_type.value,
            "target_column": profile.target_column,
            "primary_metric": profile.primary_metric.value,
            "dropped_columns": [],
            "preprocessing": [],
            "candidate_models": [{"name": "X", "library": "Y", "rationale": "Z"}],
            "validation_strategy": "x",
            "analysis_summary": "x",
            "risks": [],
            "code": "x",
        }
    )


def test_gen_result_validation_error_message_is_not_swallowed():
    """pydantic.ValidationError must actually be caught by generate(), not
    just json.JSONDecodeError - well-formed JSON that violates the schema
    (too few candidate_models) is the more likely failure in practice than
    unparseable text."""
    payload = json.dumps(
        {
            "problem_type": "binary_classification",
            "target_column": "target",
            "primary_metric": "f1",
            "dropped_columns": [],
            "preprocessing": [],
            "candidate_models": [{"name": "X", "library": "Y", "rationale": "Z"}],
            "validation_strategy": "x",
            "analysis_summary": "x",
            "risks": [],
            "code": "x",
        }
    )
    with pytest.raises(ValidationError):
        GenResult.model_validate_json(payload)


def test_schema_violation_also_triggers_repair(profile):
    """A ValidationError from a below-minimum candidate_models list must be
    caught the same way a JSONDecodeError is - both are "invalid output",
    and only one of them fails to parse as JSON at all."""
    good = _valid_gen_result_json(profile)
    provider = _ScriptedProvider(texts=[_schema_violating_json(profile), good])

    result = llm.generate(profile, "ds-schema-repair", provider)

    assert provider.calls == 2
    assert result.target_column == profile.target_column
    rows = storage.get_generations("ds-schema-repair")
    assert [row["state"] for row in rows] == ["failed", "success"]


# --- Key rotation ------------------------------------------------------------
#
# Rotation and failover are the two halves of multi-key support and they fail
# in opposite directions: rotation that does not rotate quietly drains one key
# while the others idle, and failover that is too eager burns a second key's
# quota on an error a second key cannot fix. Both need holding down.


def _rotating(keys: list[str], behaviour):
    """A GeminiProvider whose per-key call is replaced by `behaviour`.

    Subclassing rather than patching genai: these tests are about which key is
    chosen and when, so the network layer should not be constructed at all.
    """

    class _Provider(llm.GeminiProvider):
        def _generate_with_key(self, api_key, *, system_prompt, user_message):
            return behaviour(api_key)

    return _Provider(api_keys=keys, model=settings.llm_model, timeout_s=1)


def _ok(_api_key: str) -> llm.RawGeneration:
    return llm.RawGeneration(text="{}", input_tokens=1, output_tokens=1)


def _rate_limited(_api_key: str) -> llm.RawGeneration:
    raise AppError(ErrorCode.LLM_RATE_LIMITED, "429", {"provider_status": "429"})


def test_successive_calls_rotate_across_every_key():
    seen: list[str] = []
    keys = ["k1", "k2", "k3"]
    provider = _rotating(keys, lambda key: (seen.append(key), _ok(key))[1])

    for _ in range(len(keys)):
        provider.generate(system_prompt="s", user_message="u")

    assert sorted(seen) == sorted(keys)


def test_a_rate_limited_key_fails_over_to_the_next_one():
    tried: list[str] = []

    def behaviour(api_key: str) -> llm.RawGeneration:
        tried.append(api_key)
        if len(tried) < 3:
            return _rate_limited(api_key)
        return _ok(api_key)

    result = _rotating(["k1", "k2", "k3"], behaviour).generate(
        system_prompt="s", user_message="u"
    )

    assert result.text == "{}"
    assert len(tried) == 3
    assert len(set(tried)) == 3


def test_every_key_rate_limited_reports_how_many_were_tried():
    with pytest.raises(AppError) as exc_info:
        _rotating(["k1", "k2", "k3"], _rate_limited).generate(
            system_prompt="s", user_message="u"
        )

    assert exc_info.value.code is ErrorCode.LLM_RATE_LIMITED
    assert exc_info.value.details["keys_tried"] == "3"


def test_a_non_quota_failure_does_not_spend_a_second_key():
    tried: list[str] = []

    def behaviour(api_key: str) -> llm.RawGeneration:
        tried.append(api_key)
        raise AppError(ErrorCode.LLM_UNAVAILABLE, "503", {})

    with pytest.raises(AppError) as exc_info:
        _rotating(["k1", "k2", "k3"], behaviour).generate(system_prompt="s", user_message="u")

    assert exc_info.value.code is ErrorCode.LLM_UNAVAILABLE
    assert len(tried) == 1


def test_duplicate_keys_are_collapsed(monkeypatch):
    # Two slots holding the same key look like two quotas and are one; the
    # rotation would "fail over" onto the key that just returned 429.
    monkeypatch.setattr(llm.settings, "google_api_key", "same")
    monkeypatch.setattr(llm.settings, "google_api_key1", "same")
    monkeypatch.setattr(llm.settings, "google_api_key2", "other")
    monkeypatch.setattr(llm.settings, "google_api_key3", "")

    assert llm.settings.google_api_key_list == ["same", "other"]
