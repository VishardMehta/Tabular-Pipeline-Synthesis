"""The dtype classification ladder. Seven rungs, first match wins.

Not prompt surface.

Each rung produces exactly one InferredType, in this fixed order:

  0. no non-null values           -> UNKNOWN   (nothing to test; ALL_MISSING)
  1. boolean vocabulary           -> BOOLEAN
  2. datetime parse-rate test     -> DATETIME
  3. numeric, native or coerced   -> NUMERIC_DISCRETE or NUMERIC_CONTINUOUS
  4. near-unique object column    -> TEXT
  5. everything else object-typed -> CATEGORICAL
  6. unreachable in practice      -> UNKNOWN (guard only)

Rungs 4 and 5 together resolve a gap heuristics.md does not cover: nothing
names a constant that separates a categorical label from free text. Rather
than invent one, this reuses ID_UNIQUENESS. A string column that is
near-unique is either an identifier or free text, and either way a fixed
small set of levels is not what it has, so it becomes TEXT. Below that
threshold it stays CATEGORICAL, where it can still earn HIGH_CARDINALITY
without ever being confused for an open text field. This is a decision made
in the absence of a spec, not a discovery, and it is called out as such.

Rung 3's coercion (object column that is really numbers wearing currency
symbols, thousands separators, or padding) is the same test, and the same
PARSE_RATE constant, as rung 2's datetime test. See PARSE_RATE's comment:
"one threshold, two rungs of the ladder."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app import heuristics
from app.models import ColumnFlag, InferredType

# Canonical two-value vocabularies. A column's casefolded, stripped unique
# values must be a non-empty subset of exactly one of these pairs. Deliberately
# narrow: a two-category column like {"red", "blue"} is a real categorical, not
# a boolean wearing color names, and guessing wrong here would make the
# generated code treat two colors as True/False.
_BOOLEAN_VOCABULARIES: tuple[frozenset[str], ...] = (
    frozenset({"true", "false"}),
    frozenset({"1", "0"}),
    frozenset({"yes", "no"}),
    frozenset({"y", "n"}),
    frozenset({"t", "f"}),
)

# Symbols stripped before attempting numeric coercion on an object column.
# Currency signs and thousands separators are the two things that turn a real
# number into a string in an ordinary export. The percent sign is stripped
# without rescaling the value; treating "12%" as 12 rather than 0.12 is a
# documented simplification, not an attempt at unit inference.
_NUMERIC_CLEAN_PATTERN = re.compile(r"[,$£€¥%\s]")


@dataclass(frozen=True)
class DtypeResult:
    """What the ladder decided about one column."""

    inferred_type: InferredType
    flags: list[ColumnFlag]
    # The values to compute unique_count/unique_pct/top_value_pct/numeric
    # summary stats from. For NUMERIC_AS_STRING this is the cleaned numeric
    # series, not the raw strings, because the raw string cardinality
    # ("$1,000.00" vs "$1000.00") is noise the coercion already resolved.
    # None means: use the original series as-is.
    effective_values: pd.Series | None
    parse_rate: float | None


def _boolean_match(unique_values: pd.Index, is_numeric_dtype: bool) -> bool:
    if len(unique_values) == 0:
        return False
    if is_numeric_dtype:
        return len(unique_values) <= 2 and set(unique_values) <= {0, 1}
    # Normalize before counting, not after: "Yes", "yes" and " No " are three
    # raw strings but two boolean values, and checking length on the raw set
    # would reject every column whose casing is not perfectly consistent,
    # which is most of them.
    normalized = {str(v).strip().casefold() for v in unique_values}
    if len(normalized) > 2:
        return False
    return any(normalized <= vocab for vocab in _BOOLEAN_VOCABULARIES)


def _sample_for_parse_test(non_null: pd.Series, rng: np.random.Generator) -> pd.Series:
    """DTYPE_SAMPLE_N rows, randomly, never a head slice.

    A head slice is biased by exactly the things that make real files messy: a
    leading block of nulls, a differently formatted first section, rows sorted
    by date. See DTYPE_SAMPLE_N's comment.
    """
    if len(non_null) <= heuristics.DTYPE_SAMPLE_N:
        return non_null
    positions = rng.choice(len(non_null), size=heuristics.DTYPE_SAMPLE_N, replace=False)
    return non_null.iloc[positions]


def _datetime_parse_rate(non_null: pd.Series, rng: np.random.Generator) -> float:
    sample = _sample_for_parse_test(non_null, rng)
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return float(parsed.notna().mean())


def _numeric_coerced(non_null: pd.Series) -> pd.Series:
    cleaned = non_null.astype(str).str.strip().str.replace(_NUMERIC_CLEAN_PATTERN, "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _numeric_parse_rate(non_null: pd.Series, rng: np.random.Generator) -> tuple[float, pd.Series]:
    sample = _sample_for_parse_test(non_null, rng)
    coerced_sample = _numeric_coerced(sample)
    rate = float(coerced_sample.notna().mean())
    return rate, coerced_sample


def classify(series: pd.Series, rng: np.random.Generator) -> DtypeResult:
    """Run the ladder on one column. Assumes at least one non-null value."""
    non_null = series.dropna()
    unique_values = pd.Index(non_null.unique())
    is_numeric_dtype = pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(
        series
    )

    # Rung 1: BOOLEAN
    if pd.api.types.is_bool_dtype(series) or _boolean_match(unique_values, is_numeric_dtype):
        return DtypeResult(InferredType.BOOLEAN, [], None, None)

    # Rung 3 (native numeric): dtype is already int64/float64.
    if is_numeric_dtype:
        n_unique = int(non_null.nunique())
        kind = (
            InferredType.NUMERIC_DISCRETE
            if n_unique <= heuristics.NUMERIC_DISCRETE_MAX_UNIQUE
            else InferredType.NUMERIC_CONTINUOUS
        )
        return DtypeResult(kind, [], None, None)

    # From here the column is object dtype. Rungs 2 and 3 both sample and both
    # read PARSE_RATE; try datetime first since a numeric coercion of a date
    # string reliably fails anyway (mixed non-digit separators), so there is no
    # ordering ambiguity between the two.
    parse_rng = np.random.default_rng(rng.integers(0, 2**32 - 1))
    datetime_rate = _datetime_parse_rate(non_null, parse_rng)
    if datetime_rate >= heuristics.PARSE_RATE:
        return DtypeResult(InferredType.DATETIME, [], None, datetime_rate)

    numeric_rate, _ = _numeric_parse_rate(non_null, parse_rng)
    if numeric_rate >= heuristics.PARSE_RATE:
        coerced_full = _numeric_coerced(non_null)
        n_unique = int(coerced_full.nunique())
        kind = (
            InferredType.NUMERIC_DISCRETE
            if n_unique <= heuristics.NUMERIC_DISCRETE_MAX_UNIQUE
            else InferredType.NUMERIC_CONTINUOUS
        )
        return DtypeResult(
            kind, [ColumnFlag.NUMERIC_AS_STRING], coerced_full, numeric_rate
        )

    # Rungs 4 and 5: CATEGORICAL vs TEXT, decided by ID_UNIQUENESS. See the
    # module docstring for why this constant and not a dedicated one.
    unique_pct = len(unique_values) / len(series)
    if unique_pct >= heuristics.ID_UNIQUENESS:
        return DtypeResult(InferredType.TEXT, [], None, None)

    return DtypeResult(InferredType.CATEGORICAL, [], None, None)
