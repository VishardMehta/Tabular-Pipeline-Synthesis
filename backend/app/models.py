"""Pydantic v2 schemas. This module is the contract between every layer.

Everything else in the system derives from this file: the API responses, the
TypeScript mirrors in the frontend, the Gemini `response_schema`, and the
validator's self-consistency checks. Changing a field here is a breaking change
in four places at once.

Design rule inherited from the architecture: Python computes facts, the LLM
reasons over facts, the LLM never sees raw data. That is why no model in this
file carries cell values, category labels, or sample rows. Only derived
statistics cross the boundary into a prompt.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.heuristics import ANALYSIS_SUMMARY_MAX_CHARS, RISKS_MAX_ITEMS

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ProblemType(StrEnum):
    """The supervised task inferred from the target column."""

    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"


class Metric(StrEnum):
    """Closed set of primary metrics.

    Closed rather than free text so the LLM cannot invent a metric that the
    validator has no rule for, and so the frontend can label it confidently.
    Selection is driven by the balance bands in heuristics.py.
    """

    ACCURACY = "accuracy"
    F1 = "f1"
    F1_MACRO = "f1_macro"
    PR_AUC = "pr_auc"
    ROC_AUC = "roc_auc"
    RMSE = "rmse"
    MAE = "mae"
    R2 = "r2"


class InferredType(StrEnum):
    """Output of the dtype classification ladder.

    Deliberately not the pandas dtype. A column stored as int64 may be a
    boolean flag, an identifier, or a genuine count, and the preprocessing
    implied by each is different.
    """

    BOOLEAN = "boolean"
    DATETIME = "datetime"
    NUMERIC_DISCRETE = "numeric_discrete"
    NUMERIC_CONTINUOUS = "numeric_continuous"
    CATEGORICAL = "categorical"
    TEXT = "text"
    UNKNOWN = "unknown"


class ColumnFlag(StrEnum):
    """Advisory findings attached to a column by the profiler.

    A flag is a fact with a threshold behind it, never a decision. Dropping a
    column is the LLM's call in GenResult.dropped_columns; the profiler only
    reports. Every member here maps to exactly one constant in heuristics.py.
    """

    ALL_MISSING = "all_missing"
    HIGH_MISSING = "high_missing"
    CONSTANT = "constant"
    QUASI_CONSTANT = "quasi_constant"
    ID_LIKE = "id_like"
    HIGH_CARDINALITY = "high_cardinality"
    NUMERIC_AS_STRING = "numeric_as_string"
    POTENTIAL_LEAKAGE = "potential_leakage"


class ValidationSeverity(StrEnum):
    """Severity of a static validation finding.

    ERROR means the generated code is unsafe or provably broken and must be
    surfaced as a failure. WARNING means it is likely wrong but runnable. INFO
    is an observation that does not undermine the pipeline.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class JobState(StrEnum):
    """Lifecycle of one dataset through the MVP-1 flow.

    Five working states plus a terminal failure. There is no EXECUTING state:
    MVP-1 does not run generated code, and MVP-1.5 execution is a separate
    opt-in step rather than a stage of this pipeline.
    """

    PENDING = "pending"
    PROFILING = "profiling"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------


class ColumnProfile(BaseModel):
    """Computed facts about a single column.

    Contains no values from the file. Statistics only, so that a ProfileCard
    can be placed in a prompt without leaking the user's data.
    """

    name: str
    inferred_type: InferredType
    pandas_dtype: str = Field(description="The dtype pandas actually assigned, for debugging.")

    missing_count: int
    missing_pct: float = Field(ge=0.0, le=1.0)
    unique_count: int
    unique_pct: float = Field(
        ge=0.0, le=1.0, description="unique_count / n_rows. Backs the ID_LIKE decision."
    )

    # Share of non-null rows held by the single most common value. Backs
    # QUASI_CONSTANT. Not the value itself, which would be raw data.
    top_value_pct: float | None = Field(default=None, ge=0.0, le=1.0)

    # Up to five distinct level names, for low-cardinality categoricals only.
    #
    # This is the one place values from the file cross into the prompt, and it
    # is metadata rather than data: the same thing a data dictionary would
    # publish. Without it the model cannot tell an ordinal scale from a nominal
    # one, cannot see whether a binary column reads Y/N or Yes/No or 1/0, and
    # writes mapping code that fails on contact with the file.
    #
    # Populate only when inferred_type is CATEGORICAL and unique_count is at or
    # below SAMPLE_VALUES_MAX_UNIQUE. Never for TEXT, never for numeric, and
    # never for a column flagged ID_LIKE or HIGH_CARDINALITY, since those are
    # the cases where a level name is a real identifier rather than a label.
    # Truncate each value to SAMPLE_VALUE_MAX_CHARS characters.
    sample_values: list[str] | None = None

    # Numeric summary. None for non-numeric columns.
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    std: float | None = None
    median: float | None = None

    # Fraction of sampled non-null values that parsed as datetimes. Only set
    # when the datetime rung of the ladder was reached. Backs PARSE_RATE.
    parse_rate: float | None = Field(default=None, ge=0.0, le=1.0)

    # Strength of association with the target, on a sample, as an absolute
    # value in 0.0-1.0 so both directions register. Backs POTENTIAL_LEAKAGE.
    # None for the target column itself and when the target is unknown.
    #
    # The statistic behind this number is per task type, and stage 2 must
    # branch rather than reach for one correlation everywhere. Spearman or
    # Pearson against a regression target. Point-biserial for a numeric feature
    # against a binary target. A level-to-class purity measure for a
    # categorical feature against any classification target, because rank
    # correlation presumes an ordered target and nominal class labels have no
    # order, which makes Spearman meaningless on multiclass.
    target_association: float | None = Field(default=None, ge=0.0, le=1.0)

    flags: list[ColumnFlag] = Field(default_factory=list)


class ProfileCard(BaseModel):
    """The complete factual description of a dataset.

    This is the only object llm.py accepts. It never accepts a DataFrame.
    """

    dataset_id: str
    filename: str

    n_rows: int
    n_columns: int

    target_column: str
    problem_type: ProblemType
    task_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="How sure the inference ladder is about problem_type. Surfaced to the user "
        "so a wrong inference is correctable rather than silent.",
    )
    primary_metric: Metric

    # Always populated, by the same function that picks the primary.
    #
    # Recommending F1 while suppressing accuracy is the black-box behaviour this
    # tool exists to argue against: the user cannot tell whether the headline
    # metric was chosen to flatter the result. Showing the others alongside it
    # makes the choice inspectable rather than authoritative.
    #
    # This is also where roc_auc lives. It is a useful secondary on binary
    # classification and a poor primary under imbalance, which is exactly why no
    # band selects it.
    secondary_metrics: list[Metric] = Field(default_factory=list)

    # Majority-to-minority class ratio for classification. None for
    # regression. Drives metric selection via the balance bands.
    class_balance_ratio: float | None = Field(default=None, ge=1.0)

    duplicate_row_count: int = 0

    # Honest reporting of whether the numbers above are exact. Set when
    # n_rows exceeds SAMPLE_THRESHOLD.
    profiled_on_sample: bool = False
    sample_rows: int | None = None

    columns: list[ColumnProfile]


# ---------------------------------------------------------------------------
# Generation result
# ---------------------------------------------------------------------------


class DroppedColumn(BaseModel):
    """A column the strategy excludes from the feature set, and why."""

    column: str
    reason: str


class PreprocessingStep(BaseModel):
    """One transformation in the pipeline, with the columns it applies to."""

    step: str = Field(description="Short name, for example 'median imputation'.")
    columns: list[str]
    rationale: str


class CandidateModel(BaseModel):
    """A model the strategy proposes trying.

    Carries no score field of any kind. See the note on GenResult.
    """

    name: str
    library: str
    rationale: str


# GenResult field order is load-bearing and must not be reordered.
#
# The model generates fields in declaration order, so every strategy decision -
# problem type, target, metric, drops, preprocessing, candidates, validation
# strategy, summary, risks - is committed to before the first line of `code` is
# written. The code is then a transcription of a plan that already exists in the
# context rather than an improvisation the strategy is retrofitted onto.
# Reordering this class silently removes that effect while leaving every test
# passing.
#
# There is also no field here capable of holding a metric value, and none may be
# added. MVP-1 does not execute the generated code, so any score, accuracy, or
# expected performance figure the model produced would be fabricated, and it
# would arrive wearing the same formatting as a measured one.
class GenResult(BaseModel):
    """The LLM's complete response: a strategy, then the code implementing it."""

    problem_type: ProblemType
    target_column: str
    primary_metric: Metric
    dropped_columns: list[DroppedColumn]
    preprocessing: list[PreprocessingStep]
    candidate_models: list[CandidateModel]
    validation_strategy: str
    analysis_summary: str = Field(max_length=ANALYSIS_SUMMARY_MAX_CHARS)
    # max_length on a list bounds the number of items, not their length.
    risks: list[str] = Field(max_length=RISKS_MAX_ITEMS)
    code: str


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class ValidationCheck(BaseModel):
    """One static check applied to generated code or to the strategy."""

    check_id: str = Field(description="Stable identifier, for example 'ast_import_allowlist'.")
    title: str
    severity: ValidationSeverity
    passed: bool
    message: str
    details: list[str] = Field(
        default_factory=list,
        description="Offending symbols, column names, or line references.",
    )


class ValidationReport(BaseModel):
    """The full checklist rendered on Screen 4."""

    passed: bool = Field(description="True when no check of ERROR severity failed.")
    error_count: int = 0
    warning_count: int = 0
    checks: list[ValidationCheck]


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Machine-readable failure description.

    `code` is a string here rather than an enum because the full code
    enumeration lives in errors.py from stage 1 onward, and models.py must not
    depend on it.
    """

    code: str
    message: str = Field(description="Written for a human to act on, not a stack trace.")
    retryable: bool = False
    details: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Every non-2xx response body in the API has this shape."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# API request and response bodies
# ---------------------------------------------------------------------------


class DatasetUploadResponse(BaseModel):
    """Result of POST /api/datasets. Feeds the target selection screen."""

    dataset_id: str
    filename: str
    n_rows: int
    n_columns: int
    columns: list[str]
    state: JobState


class ProfileRequest(BaseModel):
    """Body of POST /api/datasets/{id}/profile."""

    target_column: str


class ProfileResponse(BaseModel):
    """Result of POST /api/datasets/{id}/profile."""

    state: JobState
    profile: ProfileCard


class GenerateRequest(BaseModel):
    """Body of POST /api/datasets/{id}/generate.

    Empty by design, and it must stay empty.

    The profile is already stored server side. Accepting a client-supplied
    ProfileCard here would let the caller rewrite the facts the LLM reasons
    over, which breaks the premise the whole system rests on: that Python
    computes the facts and the model only reasons about them. A caller who can
    edit the profile can make the model justify any pipeline at all, and the
    validator's self-consistency check would pass, because it compares the
    result against the same forged profile.
    """


class GenerateResponse(BaseModel):
    """Result of POST /api/datasets/{id}/generate."""

    state: JobState
    result: GenResult
    validation: ValidationReport


class HealthResponse(BaseModel):
    """Result of GET /api/health."""

    status: str
    version: str
