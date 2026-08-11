"""Assembling a ProfileCard from a parsed DataFrame and a chosen target.

Not prompt surface.

Architectural rule for this whole module, agreed before writing it: sampling
bounds only expensive O(n*m) work. Ingest already parses and holds the full
frame in memory to run the memory-limit check, so every cheap per-column
statistic - nunique, isna, value_counts, dtype checks - runs on the full frame,
always, regardless of size. SAMPLE_THRESHOLD gates exactly one thing here: the
leakage correlation between each feature and the target. It does not gate
dtype classification's own DTYPE_SAMPLE_N sampling, which is unconditional at
any file size because it is a fixed, cheap way to avoid running per-value
format inference across a whole column, not a fallback for large files.

This makes ProfileCard.profiled_on_sample's meaning narrower than its
docstring originally implied: true means the leakage correlations were
computed on a subsample of rows, nothing broader. See the field's updated
docstring in models.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app import heuristics, leakage, metrics
from app.dtypes import DtypeResult, classify
from app.errors import AppError, ErrorCode
from app.models import ColumnFlag, ColumnProfile, InferredType, ProblemType, ProfileCard

# Any fixed seed keeps profiling deterministic across reruns of the same file,
# which is the property that matters; the particular number carries no
# tradeoff of its own, unlike the thresholds in heuristics.py, so it lives here
# rather than being promoted to a named constant there.
_RNG_SEED = 42

_NUMERIC_TYPES = (InferredType.NUMERIC_DISCRETE, InferredType.NUMERIC_CONTINUOUS)
_CATEGORICAL_LIKE_TYPES = (InferredType.BOOLEAN, InferredType.CATEGORICAL)
_MODELABLE_TARGET_TYPES = (*_NUMERIC_TYPES, InferredType.BOOLEAN, InferredType.CATEGORICAL)


def _effective(series: pd.Series, result: DtypeResult) -> pd.Series:
    """The values a column's statistics should be computed from.

    Ordinarily the original series. For a column the ladder coerced out of
    text (NUMERIC_AS_STRING), the cleaned numeric values - reporting
    cardinality or a mean from "$1,200.50" style strings would describe the
    noise in the encoding, not the data.
    """
    return result.effective_values if result.effective_values is not None else series


def _map_problem_type(
    inferred_type: InferredType, unique_count: int
) -> tuple[ProblemType, float]:
    """Target type to problem type. See heuristics.py's Task inference section
    for why the confidence values differ between branches. Only reachable for
    types in _MODELABLE_TARGET_TYPES; the caller raises TARGET_TYPE_UNSUPPORTED
    before this for anything else."""
    if inferred_type is InferredType.BOOLEAN:
        return ProblemType.BINARY_CLASSIFICATION, heuristics.TASK_CONFIDENCE_TYPE_MATCH
    if inferred_type is InferredType.CATEGORICAL:
        problem = (
            ProblemType.BINARY_CLASSIFICATION
            if unique_count == 2
            else ProblemType.MULTICLASS_CLASSIFICATION
        )
        return problem, heuristics.TASK_CONFIDENCE_TYPE_MATCH
    if inferred_type is InferredType.NUMERIC_CONTINUOUS:
        return ProblemType.REGRESSION, heuristics.TASK_CONFIDENCE_TYPE_MATCH
    # NUMERIC_DISCRETE
    problem = (
        ProblemType.BINARY_CLASSIFICATION
        if unique_count == 2
        else ProblemType.MULTICLASS_CLASSIFICATION
    )
    return problem, heuristics.TASK_CONFIDENCE_DISCRETE_AMBIGUOUS


def _validate_target(frame: pd.DataFrame, target_column: str) -> None:
    if target_column not in frame.columns:
        raise AppError(
            ErrorCode.TARGET_NOT_FOUND,
            f"Column '{target_column}' does not exist in this dataset.",
            {"target_column": target_column},
        )
    non_null = frame[target_column].dropna()
    if len(non_null) == 0:
        raise AppError(
            ErrorCode.TARGET_ALL_NULL,
            f"'{target_column}' has no non-null values. Choose a different target.",
            {"target_column": target_column},
        )
    if non_null.nunique() < 2:
        raise AppError(
            ErrorCode.TARGET_SINGLE_VALUE,
            f"'{target_column}' has only one distinct value. A target needs at "
            "least two to be predictable.",
            {"target_column": target_column},
        )


def _leakage_association(
    feature_type: InferredType,
    problem_type: ProblemType,
    feature_values: pd.Series,
    target_values: pd.Series,
) -> float | None:
    if feature_type in _NUMERIC_TYPES:
        if problem_type is ProblemType.REGRESSION:
            return leakage.spearman(feature_values, target_values)
        return leakage.correlation_ratio(feature_values, target_values)
    if feature_type in _CATEGORICAL_LIKE_TYPES:
        if problem_type is ProblemType.REGRESSION:
            return leakage.correlation_ratio(target_values, feature_values)
        return leakage.purity(feature_values, target_values)
    # TEXT, DATETIME, UNKNOWN: correlating raw text or timestamps is not
    # meaningful without feature engineering that has not happened yet.
    return None


def _numeric_summary(values: pd.Series) -> dict[str, float | None]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) == 0:
        return {"min": None, "max": None, "mean": None, "std": None, "median": None}
    return {
        "min": float(clean.min()),
        "max": float(clean.max()),
        "mean": float(clean.mean()),
        "std": float(clean.std()) if len(clean) > 1 else 0.0,
        "median": float(clean.median()),
    }


def _build_column_profile(
    name: str,
    series: pd.Series,
    n_rows: int,
    *,
    is_target: bool,
    problem_type: ProblemType | None,
    target_for_leakage: pd.Series | None,
    rng: np.random.Generator,
) -> ColumnProfile:
    """Build one column's profile.

    target_for_leakage, when given, is already scoped to whatever rows the
    caller decided to compare against - the full frame, or the shared sample
    when profiled_on_sample is true. This function does not know or care which;
    it reindexes this column's own values to match and lets the leakage
    functions drop whatever does not line up.
    """
    missing_count = int(series.isna().sum())
    missing_pct = missing_count / n_rows

    if missing_count == n_rows:
        return ColumnProfile(
            name=name,
            inferred_type=InferredType.UNKNOWN,
            pandas_dtype=str(series.dtype),
            missing_count=missing_count,
            missing_pct=1.0,
            unique_count=0,
            unique_pct=0.0,
            flags=[ColumnFlag.ALL_MISSING],
        )

    result = classify(series, rng)
    basis = _effective(series, result)
    non_null_basis = basis.dropna()

    unique_count = int(non_null_basis.nunique())
    unique_pct = unique_count / n_rows
    value_counts = non_null_basis.value_counts()
    top_value_pct = (
        float(value_counts.iloc[0] / len(non_null_basis)) if len(value_counts) else None
    )

    flags = list(result.flags)
    if 0 < missing_count < n_rows and missing_pct > heuristics.HIGH_MISSING_P:
        flags.append(ColumnFlag.HIGH_MISSING)

    if unique_count == 1:
        flags.append(ColumnFlag.CONSTANT)
    elif (
        not is_target
        and top_value_pct is not None
        and top_value_pct >= heuristics.QUASI_CONSTANT_P
    ):
        # Hard constraint from heuristics.md: never on the target. A 1%
        # positive target is the point of an imbalanced problem, not a defect.
        flags.append(ColumnFlag.QUASI_CONSTANT)

    if unique_pct >= heuristics.ID_UNIQUENESS:
        flags.append(ColumnFlag.ID_LIKE)

    if result.inferred_type is InferredType.CATEGORICAL and (
        unique_count > heuristics.HIGH_CARD_ABS or unique_pct > heuristics.HIGH_CARD_REL
    ):
        flags.append(ColumnFlag.HIGH_CARDINALITY)

    numeric_summary: dict[str, float | None] = {
        "min": None,
        "max": None,
        "mean": None,
        "std": None,
        "median": None,
    }
    if result.inferred_type in _NUMERIC_TYPES:
        numeric_summary = _numeric_summary(non_null_basis)

    sample_values: list[str] | None = None
    if (
        result.inferred_type is InferredType.CATEGORICAL
        and unique_count <= heuristics.SAMPLE_VALUES_MAX_UNIQUE
        and ColumnFlag.ID_LIKE not in flags
        and ColumnFlag.HIGH_CARDINALITY not in flags
    ):
        top_five = value_counts.head(5).index
        sample_values = [str(v)[: heuristics.SAMPLE_VALUE_MAX_CHARS] for v in top_five]

    target_association: float | None = None
    if not is_target and problem_type is not None and target_for_leakage is not None:
        feature_for_leakage = basis.reindex(target_for_leakage.index)
        target_association = _leakage_association(
            result.inferred_type, problem_type, feature_for_leakage, target_for_leakage
        )
        if target_association is not None and target_association > heuristics.LEAKAGE_R:
            flags.append(ColumnFlag.POTENTIAL_LEAKAGE)

    return ColumnProfile(
        name=name,
        inferred_type=result.inferred_type,
        pandas_dtype=str(series.dtype),
        missing_count=missing_count,
        missing_pct=missing_pct,
        unique_count=unique_count,
        unique_pct=unique_pct,
        top_value_pct=top_value_pct,
        sample_values=sample_values,
        parse_rate=result.parse_rate,
        target_association=target_association,
        flags=flags,
        **numeric_summary,
    )


def profile(
    frame: pd.DataFrame, dataset_id: str, filename: str, target_column: str
) -> ProfileCard:
    """The stage 2 entry point. Raises AppError for anything wrong with the
    chosen target; returns a complete ProfileCard otherwise."""
    _validate_target(frame, target_column)

    n_rows = len(frame)
    rng = np.random.default_rng(_RNG_SEED)

    target_series = frame[target_column]
    target_result = classify(target_series, rng)
    if target_result.inferred_type not in _MODELABLE_TARGET_TYPES:
        raise AppError(
            ErrorCode.TARGET_TYPE_UNSUPPORTED,
            f"'{target_column}' looks like {target_result.inferred_type.value} data, "
            "which cannot be used as a modelling target. Choose a numeric or "
            "categorical column.",
            {"target_column": target_column, "inferred_type": target_result.inferred_type.value},
        )

    target_basis = _effective(target_series, target_result)
    target_unique_count = int(target_basis.dropna().nunique())
    problem_type, task_confidence = _map_problem_type(
        target_result.inferred_type, target_unique_count
    )

    r_bal = metrics.class_balance_ratio(target_basis, problem_type)
    primary_metric, secondary_metrics = metrics.select_metrics(problem_type, r_bal)

    # The one and only sample-bounded step. A single shared sample of row
    # labels, drawn once, reused for every column's leakage test - not a fresh
    # sample per column - so every feature is compared against the target over
    # the identical rows. When there is no sampling, target_for_leakage simply
    # covers every row and _build_column_profile's reindex is a no-op.
    profiled_on_sample = n_rows > heuristics.SAMPLE_THRESHOLD
    sample_rows: int | None = None
    if profiled_on_sample:
        sample_index = frame.sample(n=heuristics.SAMPLE_THRESHOLD, random_state=_RNG_SEED).index
        sample_rows = heuristics.SAMPLE_THRESHOLD
    else:
        sample_index = frame.index
    target_for_leakage = target_basis.reindex(sample_index)

    columns: list[ColumnProfile] = []
    for name in frame.columns:
        is_target = name == target_column
        columns.append(
            _build_column_profile(
                name,
                frame[name],
                n_rows,
                is_target=is_target,
                problem_type=None if is_target else problem_type,
                target_for_leakage=None if is_target else target_for_leakage,
                rng=rng,
            )
        )

    return ProfileCard(
        dataset_id=dataset_id,
        filename=filename,
        n_rows=n_rows,
        n_columns=frame.shape[1],
        target_column=target_column,
        problem_type=problem_type,
        task_confidence=task_confidence,
        primary_metric=primary_metric,
        secondary_metrics=secondary_metrics,
        class_balance_ratio=r_bal,
        duplicate_row_count=int(frame.duplicated().sum()),
        profiled_on_sample=profiled_on_sample,
        sample_rows=sample_rows,
        columns=columns,
    )
