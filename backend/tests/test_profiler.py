"""Profiler tests, driven by the fixture corpus in tests/fixtures/profiler.

Every fixture was generated with a specific property in mind, named in its
filename. These tests assert that property was actually achieved, not merely
that the profiler runs without raising.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app import heuristics, profiler
from app.errors import AppError, ErrorCode
from app.models import AssociationMethod, ColumnFlag, InferredType, Metric, ProblemType

FIXTURES = Path(__file__).parent / "fixtures" / "profiler"


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(FIXTURES / name, engine="c")


def column(card, name: str):
    return next(c for c in card.columns if c.name == name)


# --- All-null column ---------------------------------------------------------


def test_all_null_column_is_unknown_and_flagged():
    card = profiler.profile(load("all_null_column.csv"), "id", "f", "target")
    empty = column(card, "empty_col")
    assert empty.inferred_type is InferredType.UNKNOWN
    assert empty.flags == [ColumnFlag.ALL_MISSING]
    assert empty.missing_pct == 1.0
    assert empty.unique_count == 0
    assert empty.target_association is None


# --- Mixed types --------------------------------------------------------------


def test_mixed_type_column_is_not_coerced_to_numeric():
    """~15% non-numeric junk keeps the parse rate under PARSE_RATE, so the
    column must stay categorical rather than being silently half-coerced."""
    card = profiler.profile(load("mixed_types.csv"), "id", "f", "target")
    messy = column(card, "messy")
    assert messy.inferred_type is InferredType.CATEGORICAL
    assert ColumnFlag.NUMERIC_AS_STRING not in messy.flags


def test_pandas_default_na_tokens_are_already_missing_before_profiling():
    """One of the junk values in mixed_types.csv is the literal string 'n/a',
    which pandas' C engine treats as a null token on read by default - by the
    time the profiler sees this column, those rows are already NaN, not the
    string 'n/a'. This is correct behaviour to rely on, not a bug to guard."""
    card = profiler.profile(load("mixed_types.csv"), "id", "f", "target")
    messy = column(card, "messy")
    assert messy.missing_count > 0


# --- Numbers stored as strings -----------------------------------------------


def test_currency_strings_are_coerced_and_flagged():
    card = profiler.profile(load("numeric_as_string.csv"), "id", "f", "target")
    price = column(card, "price")
    assert price.inferred_type in (InferredType.NUMERIC_DISCRETE, InferredType.NUMERIC_CONTINUOUS)
    assert ColumnFlag.NUMERIC_AS_STRING in price.flags
    assert price.parse_rate == 1.0
    assert price.min is not None and price.min > 0


def test_euro_symbol_and_padded_header_both_coerce():
    card = profiler.profile(load("unicode_and_padded_headers.csv"), "id", "f", "target")
    prix = column(card, "Prix (€)")
    assert ColumnFlag.NUMERIC_AS_STRING in prix.flags
    assert prix.parse_rate == 1.0


# --- Datetime, three formats --------------------------------------------------


@pytest.mark.parametrize("col", ["date_iso", "date_us_slash", "date_long_text"])
def test_each_datetime_format_is_detected_independently(col):
    card = profiler.profile(load("datetime_three_formats.csv"), "id", "f", "target")
    result = column(card, col)
    assert result.inferred_type is InferredType.DATETIME
    assert result.parse_rate == 1.0


# --- Unicode and padded headers ----------------------------------------------


def test_header_text_survives_verbatim_into_the_profile():
    card = profiler.profile(load("unicode_and_padded_headers.csv"), "id", "f", "target")
    names = {c.name for c in card.columns}
    assert "  Padded Header  " in names
    assert "Prix (€)" in names


# --- Target validation --------------------------------------------------------


def test_single_class_target_is_rejected():
    with pytest.raises(AppError) as raised:
        profiler.profile(load("single_class_target.csv"), "id", "f", "target")
    assert raised.value.code is ErrorCode.TARGET_SINGLE_VALUE


def test_null_target_is_rejected():
    with pytest.raises(AppError) as raised:
        profiler.profile(load("null_target.csv"), "id", "f", "target")
    assert raised.value.code is ErrorCode.TARGET_ALL_NULL


def test_missing_target_column_is_rejected():
    with pytest.raises(AppError) as raised:
        profiler.profile(load("balanced.csv"), "id", "f", "does_not_exist")
    assert raised.value.code is ErrorCode.TARGET_NOT_FOUND


def test_text_target_is_rejected_rather_than_guessed():
    """A free-text or datetime target has no ProblemType that fits. Refusing
    is the honest option; guessing a confidence-weighted problem type for it
    would be exactly the kind of fabricated number this project avoids."""
    df = load("id_column.csv").rename(columns={"row_id": "target", "target": "row_id"})
    with pytest.raises(AppError) as raised:
        profiler.profile(df, "id", "f", "target")
    assert raised.value.code is ErrorCode.TARGET_TYPE_UNSUPPORTED


# --- Class balance and metric selection --------------------------------------


def test_severe_imbalance_selects_pr_auc():
    card = profiler.profile(load("severe_imbalance_50to1.csv"), "id", "f", "target")
    assert card.class_balance_ratio == pytest.approx(49.0)
    assert card.primary_metric is Metric.PR_AUC
    assert set(card.secondary_metrics) == {Metric.ACCURACY, Metric.F1, Metric.ROC_AUC}


def test_mild_imbalance_selects_f1():
    card = profiler.profile(load("mild_imbalance_2to1.csv"), "id", "f", "target")
    assert heuristics.BALANCE_ACCURACY_MAX < card.class_balance_ratio <= heuristics.BALANCE_F1_MAX
    assert card.primary_metric is Metric.F1


def test_balanced_target_selects_accuracy():
    card = profiler.profile(load("balanced.csv"), "id", "f", "target")
    assert card.class_balance_ratio <= heuristics.BALANCE_ACCURACY_MAX
    assert card.primary_metric is Metric.ACCURACY


def test_primary_metric_never_appears_in_secondary_metrics():
    for fixture in ("severe_imbalance_50to1.csv", "mild_imbalance_2to1.csv", "balanced.csv"):
        card = profiler.profile(load(fixture), "id", "f", "target")
        assert card.primary_metric not in card.secondary_metrics


def test_roc_auc_is_never_a_primary_metric():
    """No band selects it. It stays flattering under imbalance while
    precision collapses, which is exactly why it is secondary-only."""
    for fixture in ("severe_imbalance_50to1.csv", "mild_imbalance_2to1.csv", "balanced.csv"):
        card = profiler.profile(load(fixture), "id", "f", "target")
        assert card.primary_metric is not Metric.ROC_AUC


def test_regression_is_always_rmse_primary_regardless_of_skew():
    """TARGET_SKEW_THRESHOLD selects no metric, even on a target skewed well
    past it. See heuristics.py's comment on why MAE is not substituted in."""
    df = load("skewed_regression.csv")
    card = profiler.profile(df, "id", "f", "target")
    assert df["target"].skew() > heuristics.TARGET_SKEW_THRESHOLD
    assert card.primary_metric is Metric.RMSE
    assert set(card.secondary_metrics) == {Metric.MAE, Metric.R2}
    assert card.class_balance_ratio is None


# --- Cardinality and cardinality-adjacent flags ------------------------------


def test_high_cardinality_categorical_is_flagged_but_stays_categorical():
    card = profiler.profile(load("high_cardinality_categorical.csv"), "id", "f", "target")
    category = column(card, "category")
    assert category.inferred_type is InferredType.CATEGORICAL
    assert ColumnFlag.HIGH_CARDINALITY in category.flags
    assert category.unique_count > heuristics.HIGH_CARD_ABS


def test_id_column_is_text_and_id_like_not_categorical():
    """Above ID_UNIQUENESS, a string column is TEXT with ID_LIKE rather than
    CATEGORICAL with HIGH_CARDINALITY - the categorical/text boundary decided
    in dtypes.py, since heuristics.md names no constant for it directly."""
    card = profiler.profile(load("id_column.csv"), "id", "f", "target")
    row_id = column(card, "row_id")
    assert row_id.inferred_type is InferredType.TEXT
    assert ColumnFlag.ID_LIKE in row_id.flags
    assert row_id.unique_pct >= heuristics.ID_UNIQUENESS


def test_constant_column_is_flagged_and_has_no_leakage_signal():
    card = profiler.profile(load("constant_column.csv"), "id", "f", "target")
    flag_col = column(card, "flag_col")
    assert ColumnFlag.CONSTANT in flag_col.flags
    assert ColumnFlag.QUASI_CONSTANT not in flag_col.flags
    assert flag_col.target_association == 0.0


def test_quasi_constant_995_is_flagged_and_exposes_sample_values():
    card = profiler.profile(load("quasi_constant_995.csv"), "id", "f", "target")
    mostly_same = column(card, "mostly_same")
    assert ColumnFlag.QUASI_CONSTANT in mostly_same.flags
    assert ColumnFlag.CONSTANT not in mostly_same.flags
    assert mostly_same.top_value_pct >= heuristics.QUASI_CONSTANT_P
    assert set(mostly_same.sample_values) == {"North", "South"}


def test_quasi_constant_never_applies_to_the_target():
    """Hard constraint from heuristics.md: a 1%-positive target is the point
    of an imbalanced problem, not a defect in the column."""
    df = load("quasi_constant_995.csv").rename(
        columns={"target": "old_target", "mostly_same": "target"}
    )
    card = profiler.profile(df, "id", "f", "target")
    target_profile = column(card, "target")
    assert ColumnFlag.QUASI_CONSTANT not in target_profile.flags


# --- Leakage -------------------------------------------------------------


def test_leaking_feature_is_flagged():
    card = profiler.profile(load("leaking_feature.csv"), "id", "f", "target")
    leaky = column(card, "leaky")
    assert leaky.target_association > heuristics.LEAKAGE_R
    assert ColumnFlag.POTENTIAL_LEAKAGE in leaky.flags


def test_ordinary_feature_is_not_flagged_as_leaking():
    card = profiler.profile(load("leaking_feature.csv"), "id", "f", "target")
    feature = column(card, "feature")
    assert feature.target_association < heuristics.LEAKAGE_R
    assert ColumnFlag.POTENTIAL_LEAKAGE not in feature.flags


def test_target_itself_has_no_leakage_association():
    card = profiler.profile(load("leaking_feature.csv"), "id", "f", "target")
    target_profile = column(card, "target")
    assert target_profile.target_association is None
    assert ColumnFlag.POTENTIAL_LEAKAGE not in target_profile.flags


def test_leakage_association_is_never_negative_or_above_one():
    for fixture in FIXTURES.glob("*.csv"):
        df = pd.read_csv(fixture, engine="c")
        target_col = "target" if "target" in df.columns else df.columns[-1]
        try:
            card = profiler.profile(df, "id", fixture.name, target_col)
        except AppError:
            continue
        for col in card.columns:
            if col.target_association is not None:
                assert 0.0 <= col.target_association <= 1.0, (fixture.name, col.name)


# --- association_method: which formula produced target_association ----------


def test_association_method_is_none_exactly_when_association_is_none():
    """The invariant documented on ColumnProfile.association_method, checked
    across every fixture rather than trusted from reading the code."""
    for fixture in FIXTURES.glob("*.csv"):
        df = pd.read_csv(fixture, engine="c")
        target_col = "target" if "target" in df.columns else df.columns[-1]
        try:
            card = profiler.profile(df, "id", fixture.name, target_col)
        except AppError:
            continue
        for col in card.columns:
            is_none = col.association_method is AssociationMethod.NONE
            assert is_none == (col.target_association is None), (fixture.name, col.name)


def test_association_method_matches_the_feature_target_pairing():
    """Numeric feature, regression target -> spearman. Numeric feature,
    classification target -> eta. Categorical feature, any target -> purity
    for classification, eta for regression, per the dispatch in profiler.py."""
    binary = profiler.profile(load("leaking_feature.csv"), "id", "f", "target")
    numeric_vs_binary = column(binary, "feature")
    assert numeric_vs_binary.association_method is AssociationMethod.ETA

    regression = profiler.profile(load("skewed_regression.csv"), "id", "f", "target")
    numeric_vs_regression = column(regression, "feature")
    assert numeric_vs_regression.association_method is AssociationMethod.SPEARMAN

    categorical_vs_binary = column(
        profiler.profile(load("high_cardinality_categorical.csv"), "id", "f", "target"),
        "category",
    )
    assert categorical_vs_binary.association_method is AssociationMethod.PURITY

    df = load("quasi_constant_995.csv").rename(
        columns={"target": "old_target", "feature": "target", "mostly_same": "category"}
    )
    categorical_vs_regression = column(
        profiler.profile(df, "id", "f", "target"), "category"
    )
    assert categorical_vs_regression.association_method is AssociationMethod.ETA


def test_association_method_is_none_for_text_and_target_columns():
    card = profiler.profile(load("id_column.csv"), "id", "f", "target")
    row_id = column(card, "row_id")
    assert row_id.inferred_type is InferredType.TEXT
    assert row_id.association_method is AssociationMethod.NONE
    assert row_id.target_association is None

    target_profile = column(card, "target")
    assert target_profile.association_method is AssociationMethod.NONE


# --- Sampling: the architectural rule, not just the old xfail's trap --------


def test_cardinality_is_never_computed_from_a_sample(monkeypatch):
    """SAMPLE_THRESHOLD bounds leakage only. unique_count must reflect the
    true full-column cardinality even when profiled_on_sample is true, or
    HIGH_CARD_REL over-flags and HIGH_CARD_ABS under-flags exactly as
    heuristics.md warns."""
    monkeypatch.setattr(heuristics, "SAMPLE_THRESHOLD", 20)

    rng = np.random.default_rng(0)
    n = 100
    df = pd.DataFrame(
        {
            "id": range(n),
            # 90 distinct values across 100 rows: a real cardinality fact that
            # a 20-row sample could not possibly reproduce correctly.
            "category": [f"L{i % 90}" for i in range(n)],
            "target": (rng.random(n) < 0.5).astype(int),
        }
    )

    card = profiler.profile(df, "id", "f", "target")
    assert card.profiled_on_sample is True
    assert card.sample_rows == 20

    category = column(card, "category")
    assert category.unique_count == 90
    assert category.unique_pct == pytest.approx(0.9)


def test_profiled_on_sample_only_affects_leakage_not_other_statistics(monkeypatch):
    """Missingness, cardinality and numeric summaries must be identical
    whether or not the leakage sampling threshold is crossed."""
    monkeypatch.setattr(heuristics, "SAMPLE_THRESHOLD", 10_000_000)
    unsampled = profiler.profile(load("balanced.csv"), "id", "f", "target")

    monkeypatch.setattr(heuristics, "SAMPLE_THRESHOLD", 50)
    sampled = profiler.profile(load("balanced.csv"), "id", "f", "target")

    assert unsampled.profiled_on_sample is False
    assert sampled.profiled_on_sample is True
    for a, b in zip(unsampled.columns, sampled.columns, strict=True):
        assert a.missing_count == b.missing_count
        assert a.unique_count == b.unique_count
        assert a.mean == b.mean


# --- Boolean vocabulary and datetime parse rate ------------------------------


@pytest.mark.parametrize(
    "values",
    [
        ["True", "False", "True", "true"],
        ["1", "0", "1", "0"],
        ["Y", "N", "Y", "Y"],
    ],
)
def test_boolean_vocabularies_are_recognized(values):
    df = pd.DataFrame({"flag": values, "id": range(len(values))})
    df["target"] = [1, 0, 1, 0]
    card = profiler.profile(df, "id", "f", "target")
    assert column(card, "flag").inferred_type is InferredType.BOOLEAN


def test_two_category_column_outside_boolean_vocab_is_not_boolean():
    """Two colors are a categorical, not a boolean wearing color names."""
    df = pd.DataFrame(
        {
            "color": ["red", "blue", "red", "blue"] * 10,
            "id": range(40),
            "target": [1, 0] * 20,
        }
    )
    card = profiler.profile(df, "id", "f", "target")
    assert column(card, "color").inferred_type is InferredType.CATEGORICAL


def test_numeric_discrete_boundary_is_inclusive():
    """Exactly NUMERIC_DISCRETE_MAX_UNIQUE distinct values is still discrete;
    one more is continuous. Confirms the ladder's comparison direction."""
    n = 200
    at_boundary = pd.DataFrame(
        {
            "id": range(n),
            "level": [i % heuristics.NUMERIC_DISCRETE_MAX_UNIQUE for i in range(n)],
            "target": [i % 2 for i in range(n)],
        }
    )
    over_boundary = pd.DataFrame(
        {
            "id": range(n),
            "level": [i % (heuristics.NUMERIC_DISCRETE_MAX_UNIQUE + 1) for i in range(n)],
            "target": [i % 2 for i in range(n)],
        }
    )
    at_card = profiler.profile(at_boundary, "id", "f", "target")
    over_card = profiler.profile(over_boundary, "id", "f", "target")
    assert column(at_card, "level").inferred_type is InferredType.NUMERIC_DISCRETE
    assert column(over_card, "level").inferred_type is InferredType.NUMERIC_CONTINUOUS


# --- Task inference confidence -----------------------------------------------


def test_categorical_and_boolean_targets_get_high_confidence():
    card = profiler.profile(load("balanced.csv"), "id", "f", "target")
    assert card.task_confidence == heuristics.TASK_CONFIDENCE_TYPE_MATCH


def test_numeric_discrete_target_gets_lower_ambiguous_confidence():
    n = 150
    rng = np.random.default_rng(3)
    df = pd.DataFrame(
        {
            "id": range(n),
            "feature": rng.normal(size=n),
            # 5 distinct integer values: could be ratings or a small count.
            "target": rng.integers(1, 6, size=n),
        }
    )
    card = profiler.profile(df, "id", "f", "target")
    assert card.problem_type is ProblemType.MULTICLASS_CLASSIFICATION
    assert card.task_confidence == heuristics.TASK_CONFIDENCE_DISCRETE_AMBIGUOUS
    assert card.task_confidence < heuristics.TASK_CONFIDENCE_TYPE_MATCH


# --- Structural invariants ----------------------------------------------------


def test_target_column_is_included_in_columns_with_no_quasi_constant_or_leakage():
    card = profiler.profile(load("balanced.csv"), "id", "f", "target")
    names = {c.name for c in card.columns}
    assert card.target_column in names
    target_profile = column(card, card.target_column)
    assert ColumnFlag.QUASI_CONSTANT not in target_profile.flags
    assert ColumnFlag.POTENTIAL_LEAKAGE not in target_profile.flags


def test_n_columns_matches_the_frame_including_target():
    df = load("balanced.csv")
    card = profiler.profile(df, "id", "f", "target")
    assert card.n_columns == df.shape[1]
    assert len(card.columns) == df.shape[1]


def test_sample_values_never_populated_for_id_like_or_high_cardinality():
    for fixture in FIXTURES.glob("*.csv"):
        df = pd.read_csv(fixture, engine="c")
        target_col = "target" if "target" in df.columns else df.columns[-1]
        try:
            card = profiler.profile(df, "id", fixture.name, target_col)
        except AppError:
            continue
        for col in card.columns:
            if col.sample_values is not None:
                assert ColumnFlag.ID_LIKE not in col.flags
                assert ColumnFlag.HIGH_CARDINALITY not in col.flags
                assert len(col.sample_values) <= 5


def test_every_fixture_profiles_without_raising_on_a_sensible_target():
    """Every generated fixture either profiles cleanly or fails with a
    specific, expected AppError - never an unhandled exception."""
    expected_errors = {
        "single_class_target.csv": ErrorCode.TARGET_SINGLE_VALUE,
        "null_target.csv": ErrorCode.TARGET_ALL_NULL,
    }
    for fixture in FIXTURES.glob("*.csv"):
        df = pd.read_csv(fixture, engine="c")
        target_col = "target" if "target" in df.columns else df.columns[-1]
        if fixture.name in expected_errors:
            with pytest.raises(AppError) as raised:
                profiler.profile(df, "id", fixture.name, target_col)
            assert raised.value.code is expected_errors[fixture.name]
        else:
            card = profiler.profile(df, "id", fixture.name, target_col)
            assert card.columns
