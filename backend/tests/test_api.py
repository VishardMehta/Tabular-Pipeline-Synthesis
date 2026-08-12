"""Contract tests for the API routes.

These assert structure, never prose. Every fixture must validate against the
real schema, and the invariants that the architecture depends on are asserted
here so a later refactor cannot quietly remove them.
"""

from __future__ import annotations

import io
import json

import pytest

from app.errors import ErrorCode
from app.models import (
    CandidateModel,
    DroppedColumn,
    GenResult,
    PreprocessingStep,
    ValidationSeverity,
)


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_returns_columns(client):
    response = client.post(
        "/api/datasets",
        files={"file": ("churn.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "churn.csv"
    assert len(body["columns"]) == body["n_columns"]


def test_upload_persists_the_dataset(client):
    """The id the client gets back has to resolve on the next request."""
    from app import storage

    body = client.post(
        "/api/datasets",
        files={"file": ("churn.csv", io.BytesIO(b"a,b\n1,2\n3,4\n"), "text/csv")},
    ).json()
    row = storage.get_dataset(body["dataset_id"])
    assert row is not None
    assert row["filename"] == "churn.csv"
    assert json.loads(row["columns_json"]) == ["a", "b"]


@pytest.mark.parametrize(
    ("payload", "status", "code"),
    [
        (b"id,age,id\n1,2,3\n", 422, "DUPLICATE_COLUMNS"),
        (b"", 422, "EMPTY_DATASET"),
        (b"a,b\n", 422, "HEADER_ONLY"),
        (b"only\n1\n", 422, "SINGLE_COLUMN"),
    ],
)
def test_ingest_rejections_use_the_error_envelope(client, payload, status, code):
    """One body shape for every failure, so the frontend never branches on which
    layer refused the request."""
    response = client.post(
        "/api/datasets",
        files={"file": ("bad.csv", io.BytesIO(payload), "text/csv")},
    )
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["retryable"] is False
    assert body["error"]["message"]


def test_rejection_message_names_the_offending_columns(client):
    """A code tells the frontend what happened. The message tells the person."""
    response = client.post(
        "/api/datasets",
        files={"file": ("bad.csv", io.BytesIO(b"id,age,id\n1,2,3\n"), "text/csv")},
    )
    assert "id" in response.json()["error"]["message"]


PROFILABLE_CSV = (
    b"id,plan,tenure,churn\n"
    + b"".join(
        f"{i},{'gold' if i % 3 else 'silver'},{i % 24},{'yes' if i % 4 == 0 else 'no'}\n".encode()
        for i in range(1, 61)
    )
)


def upload(client, payload: bytes = PROFILABLE_CSV, filename: str = "churn.csv") -> str:
    response = client.post(
        "/api/datasets", files={"file": (filename, io.BytesIO(payload), "text/csv")}
    )
    return response.json()["dataset_id"]


def test_profile_echoes_target(client):
    dataset_id = upload(client)
    response = client.post(f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"})
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["target_column"] == "churn"
    assert len(profile["columns"]) == profile["n_columns"]


def test_profile_rejects_missing_target(client):
    dataset_id = upload(client)
    response = client.post(f"/api/datasets/{dataset_id}/profile", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_profile_on_unknown_dataset_id_returns_dataset_expired(client):
    """No DATASET_NOT_FOUND exists. An id that was never uploaded gets the
    same code as one that expired - see errors.py for why that is a decision."""
    response = client.post(
        "/api/datasets/00000000-0000-4000-8000-000000000000/profile",
        json={"target_column": "churn"},
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "DATASET_EXPIRED"


def _stub_gen_result_json(*, target_column: str, problem_type: str, primary_metric: str) -> str:
    """A minimal but schema-valid GenResult, standing in for a real Gemini
    response so /generate can be exercised without a key, a cassette, or the
    network. See tests/test_llm.py for cassette-backed tests of the real
    provider and tests/conftest.py's stub_provider fixture for the wiring."""
    return GenResult(
        problem_type=problem_type,
        target_column=target_column,
        primary_metric=primary_metric,
        dropped_columns=[DroppedColumn(column="id", reason="Unique identifier, no signal.")],
        preprocessing=[
            PreprocessingStep(
                step="one-hot encoding", columns=["plan"], rationale="Nominal category."
            )
        ],
        candidate_models=[
            CandidateModel(
                name="LogisticRegression", library="scikit-learn", rationale="Baseline."
            ),
            CandidateModel(
                name="HistGradientBoostingClassifier",
                library="scikit-learn",
                rationale="Stronger default.",
            ),
        ],
        validation_strategy="Five-fold stratified cross-validation.",
        analysis_summary="A small synthetic dataset used only to exercise the API contract.",
        risks=["This is stub output for a test, not a real strategy."],
        code="import pandas as pd\ndf = pd.read_csv('data.csv', engine='c')\n",
    ).model_dump_json()


def profile_and_generate(client, stub_provider, *, target_column: str = "churn"):
    """Upload, profile, and generate against a stubbed provider - the full
    round trip /generate now depends on, since it reads back the profile
    /profile persisted rather than accepting one from the caller."""
    dataset_id = upload(client)
    profile = client.post(
        f"/api/datasets/{dataset_id}/profile", json={"target_column": target_column}
    ).json()["profile"]
    stub_provider.text = _stub_gen_result_json(
        target_column=profile["target_column"],
        problem_type=profile["problem_type"],
        primary_metric=profile["primary_metric"],
    )
    response = client.post(f"/api/datasets/{dataset_id}/generate", json={})
    return dataset_id, response


def test_generate_returns_result_and_validation(client, stub_provider):
    _, response = profile_and_generate(client, stub_provider)
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["code"]
    assert body["validation"]["checks"]


def test_generate_reads_back_the_persisted_profile_not_a_client_supplied_one(
    client, stub_provider
):
    """GenerateRequest is empty by design - nothing in the POST body can
    change which profile the model reasons over."""
    _, response = profile_and_generate(client, stub_provider)
    assert response.status_code == 200
    assert response.json()["result"]["target_column"] == "churn"


def test_generate_before_profile_returns_dataset_expired(client, stub_provider):
    """No profile on record for this id is folded into DATASET_EXPIRED - see
    the comment on _load_stored_profile in app/api/datasets.py for why."""
    dataset_id = upload(client)
    response = client.post(f"/api/datasets/{dataset_id}/generate", json={})
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "DATASET_EXPIRED"
    assert stub_provider.calls == 0


def test_generate_maps_a_provider_rate_limit_to_the_existing_code(client, stub_provider):
    from app.errors import AppError

    dataset_id = upload(client)
    client.post(f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"})
    stub_provider.error = AppError(ErrorCode.LLM_RATE_LIMITED, "slow down")

    response = client.post(f"/api/datasets/{dataset_id}/generate", json={})

    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "LLM_RATE_LIMITED"
    assert body["error"]["retryable"] is True


def test_generate_result_field_order_is_preserved_over_the_wire(client, stub_provider):
    """The plan-then-code ordering has to survive serialisation, not just the class."""
    _, response = profile_and_generate(client, stub_provider)
    assert list(response.json()["result"].keys()) == list(GenResult.model_fields.keys())


def test_gen_result_fields_carry_model_facing_descriptions():
    """Descriptions reach the model. Empty ones waste the main steering lever.

    problem_type and primary_metric are excluded because the SDK discards a
    field description on an enum-typed field when it inlines the $ref. Those
    two are steered by the ProblemType and Metric docstrings instead, which is
    asserted separately below.
    """
    undescribed = [
        name
        for name, field in GenResult.model_fields.items()
        if field.description is None and name not in {"problem_type", "primary_metric"}
    ]
    assert not undescribed, f"no description on: {undescribed}"


def test_gen_result_cannot_hold_a_metric_value():
    """MVP-1 does not execute code, so any score field would be fabricated."""
    forbidden = {"score", "accuracy", "f1", "metric_value", "expected_score", "performance"}
    assert forbidden.isdisjoint(GenResult.model_fields)


def test_profile_carries_no_raw_values_outside_sample_values(client):
    """Only low-cardinality categoricals may expose level names."""
    dataset_id = upload(client)
    response = client.post(f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"})
    for column in response.json()["profile"]["columns"]:
        values = column["sample_values"]
        if values is None:
            continue
        assert column["inferred_type"] == "categorical"
        assert len(values) <= 5
        assert "id_like" not in column["flags"]
        assert "high_cardinality" not in column["flags"]


def test_profile_reports_secondary_metrics(client):
    """A primary metric shown alone cannot be checked for whether it flatters."""
    dataset_id = upload(client)
    profile = client.post(
        f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"}
    ).json()["profile"]
    assert profile["secondary_metrics"]
    assert profile["primary_metric"] not in profile["secondary_metrics"]
    # roc_auc is a secondary on binary classification and never a primary,
    # because imbalance keeps it flattering while precision collapses.
    assert profile["primary_metric"] != "roc_auc"


def test_validation_report_counts_match_its_checks(client, stub_provider):
    """The stub's code is trivial - no Pipeline, no target reference, no
    split - so this report is expected to carry real findings, not a clean
    pass. What is asserted is the counting invariant validation.validate
    must keep regardless of content: error_count and warning_count always
    reconcile against the checks list. See tests/test_validation.py for
    checks asserted against their actual, intended failures."""
    _, response = profile_and_generate(client, stub_provider)
    report = response.json()["validation"]
    failed = [c for c in report["checks"] if not c["passed"]]
    assert report["error_count"] == sum(
        1 for c in failed if c["severity"] == ValidationSeverity.ERROR
    )
    assert report["warning_count"] == sum(
        1 for c in failed if c["severity"] == ValidationSeverity.WARNING
    )
    assert report["passed"] is (report["error_count"] == 0)


def test_cors_headers_present(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


# --- Read endpoints ----------------------------------------------------------
#
# Upload, profile and generate are all POSTs. Without a read path a browser
# refresh discarded a session whose dataset and profile were still in SQLite
# and still inside their TTL, and re-generating costs one of twenty daily
# model requests. These two GETs are that recovery path.


def test_get_dataset_returns_detail_before_profiling(client):
    dataset_id = upload(client)
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == dataset_id
    assert body["filename"] == "churn.csv"
    assert len(body["columns"]) == body["n_columns"]
    # Uploaded but not profiled is a normal point in the flow, not a failure,
    # so it is a 200 with a null profile rather than a DATASET_EXPIRED.
    assert body["profile"] is None


def test_get_dataset_returns_the_stored_profile_after_profiling(client):
    dataset_id = upload(client)
    posted = client.post(
        f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"}
    ).json()["profile"]

    body = client.get(f"/api/datasets/{dataset_id}").json()

    assert body["profile"] is not None
    # The recovery path must return the same card, not a re-derived one.
    assert body["profile"] == posted


def test_get_dataset_unknown_id_is_expired(client):
    response = client.get("/api/datasets/does-not-exist")
    assert response.status_code == 410
    assert response.json()["error"]["code"] == ErrorCode.DATASET_EXPIRED.value


def test_usage_records_every_attempt(client, stub_provider):
    dataset_id, generate_response = profile_and_generate(client, stub_provider)
    assert generate_response.status_code == 200

    body = client.get(f"/api/datasets/{dataset_id}/usage").json()

    assert body["dataset_id"] == dataset_id
    assert body["total_attempts"] == len(body["attempts"]) == 1
    attempt = body["attempts"][0]
    assert attempt["state"] == "success"
    assert attempt["attempt"] == 1
    assert attempt["latency_ms"] >= 0


def test_usage_is_empty_before_generating(client):
    dataset_id = upload(client)
    body = client.get(f"/api/datasets/{dataset_id}/usage").json()
    assert body["attempts"] == []
    assert body["total_attempts"] == 0
    assert body["total_input_tokens"] == 0


def test_usage_unknown_id_is_expired(client):
    response = client.get("/api/datasets/does-not-exist/usage")
    assert response.status_code == 410
    assert response.json()["error"]["code"] == ErrorCode.DATASET_EXPIRED.value


def test_usage_carries_no_model_performance_field(client, stub_provider):
    """Tokens and latency are measured facts about the HTTP call. A score for
    the generated pipeline is not, and must never appear - MVP-1 does not
    execute the code, so any such number would be fabricated."""
    dataset_id, _ = profile_and_generate(client, stub_provider)
    body = client.get(f"/api/datasets/{dataset_id}/usage").json()

    forbidden = {"accuracy", "score", "f1", "rmse", "auc", "r2", "metric_value"}
    for attempt in body["attempts"]:
        assert forbidden.isdisjoint(attempt.keys())


# --- Column exclusion --------------------------------------------------------
#
# The user's only lever on the pipeline used to be the target column. An
# exclusion is an instruction, not a fact - the server still computes and
# stores the whole profile, it simply stops offering that column to the model.
# That is why it does not breach the rule that GenerateRequest carries no
# profile data.


def test_generate_accepts_an_empty_exclusion_list(client, stub_provider):
    """Backwards compatibility: the field is optional and defaults to empty."""
    _, response = profile_and_generate(client, stub_provider)
    assert response.status_code == 200


def test_excluded_column_is_kept_out_of_the_prompt(client, stub_provider):
    dataset_id = upload(client)
    profile = client.post(
        f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"}
    ).json()["profile"]
    stub_provider.text = _stub_gen_result_json(
        target_column=profile["target_column"],
        problem_type=profile["problem_type"],
        primary_metric=profile["primary_metric"],
    )
    victim = next(c["name"] for c in profile["columns"] if c["name"] != "churn")

    response = client.post(
        f"/api/datasets/{dataset_id}/generate", json={"excluded_columns": [victim]}
    )

    assert response.status_code == 200
    sent = stub_provider.last_user_message
    payload = json.loads(sent[sent.index("{") : sent.rindex("}") + 1])
    assert victim not in {column["name"] for column in payload["columns"]}
    assert payload["columns_excluded_by_user"] == [victim]


def test_excluding_an_unknown_column_is_refused(client, stub_provider):
    """Silently ignoring it would leave the user believing a column was
    dropped when it was not."""
    dataset_id = upload(client)
    client.post(f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"})

    response = client.post(
        f"/api/datasets/{dataset_id}/generate", json={"excluded_columns": ["no_such_column"]}
    )

    # 422 rather than 404: the request is well formed, the named column is
    # just not in this dataset. Status comes from the table in errors.py, not
    # from the raise site.
    assert response.status_code == 422
    assert response.json()["error"]["code"] == ErrorCode.TARGET_NOT_FOUND.value
    assert stub_provider.calls == 0


def test_excluding_the_target_is_refused(client, stub_provider):
    dataset_id = upload(client)
    client.post(f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"})

    response = client.post(
        f"/api/datasets/{dataset_id}/generate", json={"excluded_columns": ["churn"]}
    )

    assert response.status_code != 200
    assert stub_provider.calls == 0


def test_the_stored_profile_still_holds_every_column_after_an_exclusion(client, stub_provider):
    """An exclusion narrows what the model is shown, never what the server
    knows. The persisted card must stay complete."""
    dataset_id = upload(client)
    profile = client.post(
        f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"}
    ).json()["profile"]
    stub_provider.text = _stub_gen_result_json(
        target_column=profile["target_column"],
        problem_type=profile["problem_type"],
        primary_metric=profile["primary_metric"],
    )
    victim = next(c["name"] for c in profile["columns"] if c["name"] != "churn")
    client.post(f"/api/datasets/{dataset_id}/generate", json={"excluded_columns": [victim]})

    stored = client.get(f"/api/datasets/{dataset_id}").json()["profile"]
    assert victim in {column["name"] for column in stored["columns"]}


# --- Concurrency guard -------------------------------------------------------


def test_a_second_concurrent_generation_is_refused(client, stub_provider):
    """The free tier allows 20 model requests per day per project per model, so
    a double-clicked button costs 10% of a day's budget for a duplicate answer.

    The first call is held inside the provider until the test releases it, which
    is the only way to have two genuinely in flight at once.
    """
    import threading

    dataset_id = upload(client)
    profile = client.post(
        f"/api/datasets/{dataset_id}/profile", json={"target_column": "churn"}
    ).json()["profile"]
    stub_provider.text = _stub_gen_result_json(
        target_column=profile["target_column"],
        problem_type=profile["problem_type"],
        primary_metric=profile["primary_metric"],
    )

    release = threading.Event()
    entered = threading.Event()
    original = stub_provider.generate

    def blocking(*, system_prompt: str, user_message: str):
        entered.set()
        release.wait(timeout=10)
        return original(system_prompt=system_prompt, user_message=user_message)

    stub_provider.generate = blocking

    first: dict = {}

    def run_first():
        first["response"] = client.post(f"/api/datasets/{dataset_id}/generate", json={})

    worker = threading.Thread(target=run_first)
    worker.start()
    try:
        assert entered.wait(timeout=10), "the first generation never reached the provider"
        second = client.post(f"/api/datasets/{dataset_id}/generate", json={})
    finally:
        release.set()
        worker.join(timeout=15)

    assert second.status_code == 429
    assert second.json()["error"]["code"] == ErrorCode.LLM_RATE_LIMITED.value
    assert first["response"].status_code == 200
    # The refused call must not have reached the provider at all - that is the
    # entire point.
    assert stub_provider.calls == 1


def test_the_guard_releases_so_a_later_generation_still_works(client, stub_provider):
    """A lock that is not released turns a one-off duplicate into a dataset
    that can never be generated again."""
    dataset_id, first = profile_and_generate(client, stub_provider)
    assert first.status_code == 200
    second = client.post(f"/api/datasets/{dataset_id}/generate", json={})
    assert second.status_code == 200
    assert stub_provider.calls == 2
