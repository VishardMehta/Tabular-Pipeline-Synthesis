"""Pydantic v2 schemas. The contract between every layer."""

# THIS FILE HAS TWO AUDIENCES. KEEP THEM SEPARATE.
#
#   `#` comments are for humans. Engineering rationale, tradeoffs, why a field
#   exists, what breaks if it changes. These never leave the repository.
#
#   Docstrings and Field(description=...) are prompt surface. They are sent to
#   the model as instruction text whenever a class here is used as a Gemini
#   `response_schema`. Model-facing wording only, no internal reasoning.
#
# This is not a style preference, it is observable. google-genai serialises the
# docstring of any class reachable from the response schema into the request as
# a `description`, so a docstring explaining a decision to a colleague becomes
# an instruction to the model.
#
# The leak has a sharp edge worth knowing before writing any description text.
# Pydantic emits a `$ref` plus a sibling `description` for enum-typed and
# single-nested-model fields. The SDK inlines the `$ref` by replacing the whole
# node, which discards the sibling. Concretely, on GenResult:
#
#   problem_type, primary_metric   Field(description=...) is SILENTLY DROPPED.
#                                  The enum's own docstring is what gets sent,
#                                  so ProblemType and Metric docstrings are the
#                                  only lever available on those two fields.
#   dropped_columns, preprocessing,
#   candidate_models               list[Model], so the field description
#                                  survives, and the nested class docstring is
#                                  sent separately as the items description.
#   everything else                plain fields, description survives normally.
#
# Everything else in this file follows from the architecture: Python computes
# facts, the LLM reasons over facts, the LLM never sees raw data. No model here
# carries cell values or sample rows. The single exception is
# ColumnProfile.sample_values, argued at its definition.

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.heuristics import ANALYSIS_SUMMARY_MAX_CHARS, RISKS_MAX_ITEMS

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


# PROMPT SURFACE. This docstring is sent, and a Field(description=...) on a
# ProblemType-typed field would be discarded, so this text is the only steering
# available on GenResult.problem_type. Stage 3 authors it properly alongside the
# system prompt. Until then it stays factual and short.
class ProblemType(StrEnum):
    """The supervised learning task for this dataset. Copy the problem_type
    given in the profile. It was derived from the target column by rule. If you
    think it is wrong, say so in `risks` rather than changing it here."""

    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"


# PROMPT SURFACE, and the same $ref trap as ProblemType: a Field description on
# GenResult.primary_metric would be dropped, so this docstring is the only lever.
#
# Rationale, for humans: the set is closed rather than free text so the model
# cannot invent a metric the validator has no rule for and the frontend cannot
# label. Which member applies is decided in Python by the balance bands in
# heuristics.py, never by the model. See heuristics.md for the selection tables
# and for why roc_auc is reachable only as a secondary.
class Metric(StrEnum):
    """An evaluation metric. Copy the primary_metric given in the profile. It
    follows from the target's class balance by rule. If you think a different
    metric suits this dataset better, say so in `risks` rather than changing it
    here."""

    ACCURACY = "accuracy"
    F1 = "f1"
    F1_MACRO = "f1_macro"
    PR_AUC = "pr_auc"
    ROC_AUC = "roc_auc"
    RMSE = "rmse"
    MAE = "mae"
    R2 = "r2"


# Not prompt surface today: ProfileCard reaches the model as serialised facts in
# the prompt body, not as a response schema, so no docstring here is sent.
#
# Deliberately not the pandas dtype. A column stored as int64 may be a boolean
# flag, an identifier, or a genuine count, and the preprocessing implied by each
# is different. The split between discrete and continuous is governed by
# NUMERIC_DISCRETE_MAX_UNIQUE.
class InferredType(StrEnum):
    """Result of the dtype classification ladder."""

    BOOLEAN = "boolean"
    DATETIME = "datetime"
    NUMERIC_DISCRETE = "numeric_discrete"
    NUMERIC_CONTINUOUS = "numeric_continuous"
    CATEGORICAL = "categorical"
    TEXT = "text"
    UNKNOWN = "unknown"


# A flag is a fact with a threshold behind it, never a decision. Dropping a
# column is the model's call in GenResult.dropped_columns; the profiler only
# reports. Every member maps to exactly one constant in heuristics.py, which is
# why there is no flag here without a number behind it.
class ColumnFlag(StrEnum):
    """Advisory finding attached to a column by the profiler."""

    ALL_MISSING = "all_missing"
    HIGH_MISSING = "high_missing"
    CONSTANT = "constant"
    QUASI_CONSTANT = "quasi_constant"
    ID_LIKE = "id_like"
    HIGH_CARDINALITY = "high_cardinality"
    NUMERIC_AS_STRING = "numeric_as_string"
    POTENTIAL_LEAKAGE = "potential_leakage"


# Which formula backs a column's target_association. See leakage.py for what
# each one actually computes; this enum exists only to name which one ran, not
# to explain it. NONE covers both "not attempted" (a TEXT, DATETIME or UNKNOWN
# feature, or the target column itself) and "attempted but no value resulted"
# (too little paired data to compute anything) - both leave
# target_association at None, and this stays paired with it.
class AssociationMethod(StrEnum):
    """Which statistic target_association measures for this column."""

    SPEARMAN = "spearman"
    ETA = "eta"
    PURITY = "purity"
    NONE = "none"


# ERROR means the generated code is unsafe or provably broken and must be
# surfaced as a failure. WARNING means it is likely wrong but runnable. INFO is
# an observation that does not undermine the pipeline.
class ValidationSeverity(StrEnum):
    """Severity of a static validation finding."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Five working states plus a terminal failure. There is no EXECUTING state:
# MVP-1 does not run generated code, and MVP-1.5 execution is a separate opt-in
# step rather than a stage of this pipeline.
class JobState(StrEnum):
    """Lifecycle of one dataset through the MVP-1 flow."""

    PENDING = "pending"
    PROFILING = "profiling"
    GENERATING = "generating"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------


# Contains no values from the file beyond sample_values, argued below.
# Statistics only, so that a ProfileCard can be placed in a prompt without
# handing the model the user's data.
class ColumnProfile(BaseModel):
    """Computed facts about a single column."""

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

    # Strength of association with the target, as an absolute value in 0.0-1.0
    # so both directions register. Backs POTENTIAL_LEAKAGE. None for the target
    # column itself and when the feature's type rules out a meaningful test
    # (TEXT, DATETIME, UNKNOWN).
    #
    # The statistic behind this number is per task type; see leakage.py. Which
    # one was used for THIS column is association_method below, not left for
    # the reader to infer from inferred_type and problem_type.
    target_association: float | None = Field(default=None, ge=0.0, le=1.0)

    # Which formula target_association is. Populated by the profiler, not
    # inferred by whoever reads this card - the profiler already knows which
    # branch it took, and re-deriving that from inferred_type and problem_type
    # is work the model would otherwise have to redo, imperfectly, on every
    # request. Always NONE exactly when target_association is None, checked in
    # test_profiler.py.
    #
    # Added after a live run showed the model describing a purity score as "a
    # weak linear association", which is a category error for all three
    # statistics leakage.py computes, none of which is a linear correlation.
    # Naming the method beside the number is a stronger fix than prohibiting
    # the wrong word in the prompt, and prompts.py does both.
    association_method: AssociationMethod = Field(default=AssociationMethod.NONE)

    flags: list[ColumnFlag] = Field(default_factory=list)


# This is the only object llm.py accepts. It never accepts a DataFrame. That
# signature is the enforcement point for the core rule, so do not widen it.
class ProfileCard(BaseModel):
    """The complete factual description of a dataset."""

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

    # Narrower than it sounds. Every column statistic in this ProfileCard -
    # cardinality, missingness, numeric summaries, flags - is always computed
    # on the full file; none of it subsamples. This field is true only when
    # n_rows exceeds SAMPLE_THRESHOLD and the leakage association
    # (target_association on each ColumnProfile) was computed on a shared
    # random sample of sample_rows rows instead of the full column, because
    # that correlation pass is the one O(n*m) step in profiling. See the
    # architectural note at the top of profiler.py.
    profiled_on_sample: bool = False
    sample_rows: int | None = None

    columns: list[ColumnProfile]


# ---------------------------------------------------------------------------
# Generation result
# ---------------------------------------------------------------------------


# PROMPT SURFACE. These three are nested under list[] fields on GenResult, so
# both the class docstring and the per-field descriptions reach the model.
# Stage 3 authors all of it against the system prompt.
class DroppedColumn(BaseModel):
    """A column excluded from the feature set, with the reason for excluding it."""

    column: str = Field(description="The column name, exactly as the profile spells it.")
    reason: str = Field(
        description="Why this column is excluded, citing the profile fact that "
        "justifies it rather than a general principle about columns of its kind."
    )


class PreprocessingStep(BaseModel):
    """One transformation applied to named columns before training."""

    step: str = Field(
        description="Short name of the transformation, for example 'median imputation'."
    )
    columns: list[str] = Field(
        description="The columns this step applies to, named exactly as the profile "
        "spells them."
    )
    rationale: str = Field(
        description="Why these columns need this transformation, grounded in their "
        "profile statistics."
    )


# Carries no score field of any kind, for the reason given above GenResult.
class CandidateModel(BaseModel):
    """A model worth trying for this dataset."""

    name: str = Field(
        description="The estimator class name, for example HistGradientBoostingClassifier."
    )
    library: str = Field(description="The library it comes from, for example scikit-learn.")
    rationale: str = Field(
        description="Why this model suits this dataset's size, shape and task. Do not "
        "state or estimate how well it would score."
    )


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
#
# Verified, not assumed. google-genai 2.17.0 emits `propertyOrdering` matching
# this declaration order at the top level and inside all three nested objects,
# and ten live generations returned the fields in this order 9 times out of 9
# that reached the model. See docs/spike-01-gemini-structured-output.md.
#
# PROMPT SURFACE below this line. The docstring becomes the schema description
# and every Field(description=...) is sent, except on problem_type and
# primary_metric where it is discarded. See the note at the top of this file.
class GenResult(BaseModel):
    """A modelling strategy for one tabular dataset, followed by the code that
    implements exactly that strategy."""

    # problem_type and primary_metric carry no description on purpose. The SDK
    # discards a Field description on an enum-typed field when it inlines the
    # $ref, so anything written here would be silently dropped. Their steering
    # lives in the ProblemType and Metric docstrings instead.
    problem_type: ProblemType
    target_column: str = Field(
        description="The column being predicted. Copy target_column from the profile "
        "exactly, preserving its original spelling, spacing and capitalisation."
    )
    primary_metric: Metric
    dropped_columns: list[DroppedColumn] = Field(
        description="Every column excluded from the feature set. This must match the "
        "columns the code actually drops, with nothing listed that the code keeps."
    )
    preprocessing: list[PreprocessingStep] = Field(
        description="The transformations applied before training, in the order the code "
        "applies them. Every retained column needing treatment should appear in a step."
    )
    candidate_models: list[CandidateModel] = Field(
        min_length=2,
        max_length=4,
        description="Two to four models worth trying on this dataset, strongest first. "
        "The first one is what the code implements.",
    )
    validation_strategy: str = Field(
        description="How the pipeline is evaluated and why that scheme suits this "
        "dataset. Name the split, the number of folds, and whether it is stratified."
    )
    analysis_summary: str = Field(
        max_length=ANALYSIS_SUMMARY_MAX_CHARS,
        description="A short plain-language account of the dataset and the strategy, for "
        "someone deciding whether to trust it. State no performance figures of any kind: "
        "this code has not been run and you have not measured anything.",
    )
    # max_length on a list bounds the number of items, not their length.
    risks: list[str] = Field(
        max_length=RISKS_MAX_ITEMS,
        description="Specific ways this pipeline could mislead or fail on this dataset, "
        "each grounded in a profile fact. General caveats true of any dataset are not "
        "risks. Include no performance figures here either.",
    )
    code: str = Field(
        description="A complete, runnable Python script implementing exactly the strategy "
        "above. Read data.csv with the pandas C engine, define every column it references, "
        "import only pandas, numpy and scikit-learn, set every random_state, and print the "
        "primary metric by name."
    )


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
