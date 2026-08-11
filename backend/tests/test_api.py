"""Contract tests for the stage 0 routes.

These assert structure, never prose. Every fixture must validate against the
real schema, and the invariants that the architecture depends on are asserted
here so a later refactor cannot quietly remove them.
"""

from __future__ import annotations

import io

import pytest

from app.models import GenResult, ValidationSeverity


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


def test_profile_echoes_target(client):
    response = client.post("/api/datasets/abc/profile", json={"target_column": "churn"})
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["target_column"] == "churn"
    assert len(profile["columns"]) == profile["n_columns"]


def test_profile_rejects_missing_target(client):
    response = client.post("/api/datasets/abc/profile", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_generate_returns_result_and_validation(client):
    response = client.post("/api/datasets/abc/generate", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["code"]
    assert body["validation"]["checks"]


def test_generate_result_field_order_is_preserved_over_the_wire(client):
    """The plan-then-code ordering has to survive serialisation, not just the class."""
    response = client.post("/api/datasets/abc/generate", json={})
    assert list(response.json()["result"].keys()) == list(GenResult.model_fields.keys())


@pytest.mark.xfail(
    strict=True,
    reason="Stage 3: author model-facing Field(description=...) on every GenResult "
    "field alongside the system prompt. Descriptions are prompt surface and are "
    "currently empty, so the schema steers generation not at all. Note that "
    "problem_type and primary_metric cannot take a field description - the SDK "
    "discards it when inlining the enum $ref - so those two are steered by the "
    "ProblemType and Metric docstrings instead.",
)
def test_gen_result_fields_carry_model_facing_descriptions():
    """Descriptions reach the model. Empty ones waste the main steering lever."""
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
    response = client.post("/api/datasets/abc/profile", json={"target_column": "churn"})
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
    profile = client.post(
        "/api/datasets/abc/profile", json={"target_column": "churn"}
    ).json()["profile"]
    assert profile["secondary_metrics"]
    assert profile["primary_metric"] not in profile["secondary_metrics"]
    # roc_auc is a secondary on binary classification and never a primary,
    # because imbalance keeps it flattering while precision collapses.
    assert profile["primary_metric"] != "roc_auc"


def test_validation_report_counts_match_its_checks(client):
    report = client.post("/api/datasets/abc/generate", json={}).json()["validation"]
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
