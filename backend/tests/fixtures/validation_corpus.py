"""Fixtures for validation.py, written before the validator.

One baseline profile and one baseline GenResult, both deliberately clean -
every check in validation.py passes against them. Every entry in CORPUS is a
copy of the baseline with exactly one thing changed, so a failing test names
exactly which behaviour broke rather than "something about validation".

Each entry names the check_id(s) expected to fail. Every other check that
runs against that entry is expected to pass - test_validation.py asserts
both halves, not just the failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import (
    CandidateModel,
    ColumnFlag,
    ColumnProfile,
    DroppedColumn,
    GenResult,
    InferredType,
    Metric,
    PreprocessingStep,
    ProblemType,
    ProfileCard,
)

# --- Baseline profile ---------------------------------------------------------
# id, plan, tenure, churn(target) - the same shape as test_api.py's
# PROFILABLE_CSV, small enough to read in one screen, sized so
# class_balance_ratio lands in the F1 band rather than accuracy or PR-AUC.

BASE_PROFILE = ProfileCard(
    dataset_id="fixture-dataset",
    filename="churn.csv",
    n_rows=100,
    n_columns=4,
    target_column="churn",
    problem_type=ProblemType.BINARY_CLASSIFICATION,
    task_confidence=0.95,
    primary_metric=Metric.F1,
    secondary_metrics=[Metric.ACCURACY, Metric.ROC_AUC],
    class_balance_ratio=2.5,
    duplicate_row_count=0,
    profiled_on_sample=False,
    sample_rows=None,
    columns=[
        ColumnProfile(
            name="id",
            inferred_type=InferredType.TEXT,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=100,
            unique_pct=1.0,
            flags=[ColumnFlag.ID_LIKE],
        ),
        ColumnProfile(
            name="plan",
            inferred_type=InferredType.CATEGORICAL,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=2,
            unique_pct=0.02,
            sample_values=["gold", "silver"],
        ),
        ColumnProfile(
            name="tenure",
            inferred_type=InferredType.NUMERIC_DISCRETE,
            pandas_dtype="int64",
            missing_count=0,
            missing_pct=0.0,
            unique_count=24,
            unique_pct=0.24,
            min=0.0,
            max=23.0,
            mean=11.0,
            std=6.0,
            median=11.0,
        ),
        ColumnProfile(
            name="churn",
            inferred_type=InferredType.CATEGORICAL,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=2,
            unique_pct=0.02,
            sample_values=["no", "yes"],
        ),
    ],
)

# --- Baseline code -------------------------------------------------------------
# Passes every check: allowlisted imports only, no dangerous calls, every
# referenced column is real, "churn" is referenced, a Pipeline and a
# ColumnTransformer, random_state everywhere it applies, a train/test split,
# and f1_score actually computed (the profile's primary metric).

GOOD_CODE = '''import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "churn"
DROP = ["id"]

df = pd.read_csv("data.csv", engine="c")

y = (df[TARGET] == "yes").astype(int)
X = df.drop(columns=[TARGET, *DROP])

numeric = ["tenure"]
categorical = ["plan"]

preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ]
)

model = Pipeline([("preprocess", preprocess), ("est", LogisticRegression(random_state=42))])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)
print(f"holdout f1: {f1_score(y_test, preds):.4f}")
'''

GOOD_RESULT = GenResult(
    problem_type=ProblemType.BINARY_CLASSIFICATION,
    target_column="churn",
    primary_metric=Metric.F1,
    dropped_columns=[DroppedColumn(column="id", reason="Unique per row, an identifier.")],
    preprocessing=[
        PreprocessingStep(step="standard scaling", columns=["tenure"], rationale="Numeric."),
        PreprocessingStep(step="one-hot encoding", columns=["plan"], rationale="Nominal category."),
    ],
    candidate_models=[
        CandidateModel(name="LogisticRegression", library="scikit-learn", rationale="Baseline."),
        CandidateModel(
            name="HistGradientBoostingClassifier",
            library="scikit-learn",
            rationale="Stronger default.",
        ),
    ],
    validation_strategy="80/20 train/test split, fixed seed.",
    analysis_summary="A small synthetic churn dataset for the validator's own fixtures.",
    risks=["This is fixture output, not a real strategy."],
    code=GOOD_CODE,
)


# --- Corpus ----------------------------------------------------------------


@dataclass(frozen=True)
class CorpusEntry:
    name: str
    result: GenResult
    # check_ids expected to fail. Every other check that actually runs
    # against this entry (i.e. is not skipped because syntax failed) is
    # expected to pass - test_validation.py asserts both directions.
    expect_failing: frozenset[str]


def _with_code(code: str) -> GenResult:
    return GOOD_RESULT.model_copy(update={"code": code})


CORPUS = [
    CorpusEntry(
        "syntax_error",
        _with_code(GOOD_CODE + "\ndf[\n"),
        frozenset({"syntax_compile"}),
    ),
    CorpusEntry(
        "forbidden_import",
        # Unused, so it cannot also trip dangerous_calls - isolates the
        # import check from the call check, which the subprocess_call entry
        # below cannot do.
        _with_code(
            GOOD_CODE.replace("import pandas as pd", "import pandas as pd\nimport requests")
        ),
        frozenset({"ast_import_allowlist"}),
    ),
    CorpusEntry(
        "exec_call",
        _with_code(GOOD_CODE + '\nexec("print(1)")\n'),
        frozenset({"dangerous_calls"}),
    ),
    CorpusEntry(
        "subprocess_call",
        # Cannot be isolated to one check: importing subprocess to call it
        # is itself an import outside the allowlist. Both checks are
        # correct, independent findings about the same two lines - see the
        # stage 4 report for why this is the one corpus entry that triggers
        # two checks by necessity rather than by a fixture design mistake.
        _with_code(GOOD_CODE + "\nimport subprocess\nsubprocess.run(['ls'])\n"),
        frozenset({"ast_import_allowlist", "dangerous_calls"}),
    ),
    CorpusEntry(
        "hallucinated_column_near_miss",
        # "tenure" -> "tenur", one character short. ratio(tenur, tenure) is
        # 0.909, above SIMILARITY_CUTOFF (0.85, from heuristics.py).
        _with_code(GOOD_CODE.replace('numeric = ["tenure"]', 'numeric = ["tenur"]')),
        frozenset({"hallucinated_columns"}),
    ),
    CorpusEntry(
        "dropped_column_still_referenced",
        # The code is untouched (still uses "plan"); the strategy just
        # claims "plan" was dropped, which the code contradicts.
        GOOD_RESULT.model_copy(
            update={
                "dropped_columns": [
                    DroppedColumn(column="id", reason="Identifier."),
                    DroppedColumn(
                        column="plan", reason="Claimed dropped, but never actually is."
                    ),
                ]
            }
        ),
        frozenset({"dropped_columns_not_referenced"}),
    ),
    CorpusEntry(
        "missing_target_reference",
        # "churn" never appears anywhere; the code reads a different,
        # nonexistent column instead. "outcome" is not close to any real
        # column (low SequenceMatcher ratio against id/plan/tenure/churn),
        # so this does not also trip hallucinated_columns.
        _with_code(
            GOOD_CODE.replace('y = (df[TARGET] == "yes").astype(int)', 'y = df["outcome"]').replace(
                'TARGET = "churn"\n', ""
            ).replace("[TARGET, *DROP]", "DROP")
        ),
        frozenset({"target_column_referenced"}),
    ),
    CorpusEntry(
        "mismatched_problem_type",
        GOOD_RESULT.model_copy(update={"problem_type": ProblemType.REGRESSION}),
        frozenset({"gen_result_self_consistency"}),
    ),
    CorpusEntry(
        "mismatched_metric",
        GOOD_RESULT.model_copy(update={"primary_metric": Metric.ACCURACY}),
        frozenset({"gen_result_self_consistency"}),
    ),
    CorpusEntry(
        "no_pipeline_or_column_transformer",
        _with_code(
            '''import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

TARGET = "churn"
DROP = ["id", "plan"]

df = pd.read_csv("data.csv", engine="c")

y = (df[TARGET] == "yes").astype(int)
X = df.drop(columns=[TARGET, *DROP])
numeric = ["tenure"]

scaler = StandardScaler()
X_scaled = X.copy()
X_scaled[numeric] = scaler.fit_transform(X[numeric])

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)
model = LogisticRegression(random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)
print(f"holdout f1: {f1_score(y_test, preds):.4f}")
'''
        ),
        frozenset({"pipeline_or_column_transformer"}),
    ),
    CorpusEntry(
        "missing_random_state",
        _with_code(
            GOOD_CODE.replace("random_state=42))", "))")
            .replace("test_size=0.2, random_state=42", "test_size=0.2")
        ),
        frozenset({"random_state_set"}),
    ),
    CorpusEntry(
        "no_split_or_cv",
        _with_code(
            '''import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "churn"
DROP = ["id"]

df = pd.read_csv("data.csv", engine="c")

y = (df[TARGET] == "yes").astype(int)
X = df.drop(columns=[TARGET, *DROP])

numeric = ["tenure"]
categorical = ["plan"]

preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ]
)

model = Pipeline([("preprocess", preprocess), ("est", LogisticRegression(random_state=42))])
model.fit(X, y)
preds = model.predict(X)
print(f"f1: {f1_score(y, preds):.4f}")
'''
        ),
        frozenset({"split_or_cross_validation"}),
    ),
    CorpusEntry(
        "metric_not_computed",
        _with_code(
            GOOD_CODE.replace(
                'print(f"holdout f1: {f1_score(y_test, preds):.4f}")',
                'print("done")',
            ).replace(
                "from sklearn.metrics import f1_score\n", ""
            )
        ),
        frozenset({"primary_metric_computed"}),
    ),
    CorpusEntry(
        "declared_column_not_in_profile",
        GOOD_RESULT.model_copy(
            update={
                "dropped_columns": [
                    DroppedColumn(column="id", reason="Identifier."),
                    DroppedColumn(column="not_a_real_column", reason="Does not exist."),
                ]
            }
        ),
        frozenset({"declared_columns_exist"}),
    ),
]
