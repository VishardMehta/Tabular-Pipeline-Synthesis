"""Hardcoded stage 0 fixtures.

Stage 0 is a walking skeleton: the routes return this module and nothing else.
Its only job is to prove that the schemas in models.py can carry a realistic
payload end to end and render on all four screens.

The fixture is deliberately awkward rather than clean. It carries a leaking
column, a numeric column stored as text, a mostly-empty free-text column, an
identifier, and a class imbalance that lands in the middle metric band, so the
frontend is built against the shapes it will actually meet rather than against
a tidy demo. Every flag here is one a real profiler run would produce.

Delete this module in stage 1. Nothing outside app/api should import it.
"""

from __future__ import annotations

from app.models import (
    AssociationMethod,
    CandidateModel,
    ColumnFlag,
    ColumnProfile,
    DatasetUploadResponse,
    DroppedColumn,
    GenResult,
    InferredType,
    JobState,
    Metric,
    PreprocessingStep,
    ProblemType,
    ProfileCard,
    ValidationCheck,
    ValidationReport,
    ValidationSeverity,
)

FIXTURE_DATASET_ID = "d1f5a9c0-0000-4000-8000-000000000001"
FIXTURE_FILENAME = "telco_churn.csv"
FIXTURE_ROWS = 7043
FIXTURE_TARGET = "churn"

FIXTURE_COLUMNS: list[str] = [
    "customer_id",
    "gender",
    "senior_citizen",
    "tenure_months",
    "contract_type",
    "monthly_charges",
    "total_charges",
    "signup_date",
    "support_tickets",
    "internal_notes",
    "churn_reason",
    "churn",
]


def upload_response(filename: str) -> DatasetUploadResponse:
    """Screen 1 result. The filename is echoed so the click-through feels real."""
    return DatasetUploadResponse(
        dataset_id=FIXTURE_DATASET_ID,
        filename=filename or FIXTURE_FILENAME,
        n_rows=FIXTURE_ROWS,
        n_columns=len(FIXTURE_COLUMNS),
        columns=FIXTURE_COLUMNS,
        state=JobState.PENDING,
    )


def _column_profiles() -> list[ColumnProfile]:
    return [
        ColumnProfile(
            name="customer_id",
            inferred_type=InferredType.TEXT,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=7043,
            unique_pct=1.0,
            flags=[ColumnFlag.ID_LIKE, ColumnFlag.HIGH_CARDINALITY],
        ),
        ColumnProfile(
            name="gender",
            inferred_type=InferredType.CATEGORICAL,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=2,
            unique_pct=0.0003,
            top_value_pct=0.505,
            sample_values=["Male", "Female"],
        ),
        ColumnProfile(
            name="senior_citizen",
            inferred_type=InferredType.BOOLEAN,
            pandas_dtype="int64",
            missing_count=0,
            missing_pct=0.0,
            unique_count=2,
            unique_pct=0.0003,
            top_value_pct=0.838,
            min=0.0,
            max=1.0,
            mean=0.162,
            std=0.369,
            median=0.0,
        ),
        ColumnProfile(
            name="tenure_months",
            inferred_type=InferredType.NUMERIC_CONTINUOUS,
            pandas_dtype="int64",
            missing_count=0,
            missing_pct=0.0,
            unique_count=73,
            unique_pct=0.0104,
            top_value_pct=0.089,
            min=0.0,
            max=72.0,
            mean=32.371,
            std=24.559,
            median=29.0,
            target_association=0.352,
            association_method=AssociationMethod.ETA,
        ),
        ColumnProfile(
            name="contract_type",
            inferred_type=InferredType.CATEGORICAL,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=3,
            unique_pct=0.0004,
            top_value_pct=0.550,
            sample_values=["Month-to-month", "One year", "Two year"],
            target_association=0.397,
            association_method=AssociationMethod.PURITY,
        ),
        ColumnProfile(
            name="monthly_charges",
            inferred_type=InferredType.NUMERIC_CONTINUOUS,
            pandas_dtype="float64",
            missing_count=0,
            missing_pct=0.0,
            unique_count=1585,
            unique_pct=0.225,
            min=18.25,
            max=118.75,
            mean=64.762,
            std=30.090,
            median=70.35,
            target_association=0.193,
            association_method=AssociationMethod.ETA,
        ),
        ColumnProfile(
            name="total_charges",
            inferred_type=InferredType.NUMERIC_CONTINUOUS,
            pandas_dtype="object",
            missing_count=11,
            missing_pct=0.0016,
            unique_count=6531,
            unique_pct=0.927,
            parse_rate=0.998,
            min=18.80,
            max=8684.80,
            mean=2283.300,
            std=2266.771,
            median=1397.475,
            target_association=0.199,
            association_method=AssociationMethod.ETA,
            flags=[ColumnFlag.NUMERIC_AS_STRING],
        ),
        ColumnProfile(
            name="signup_date",
            inferred_type=InferredType.DATETIME,
            pandas_dtype="object",
            missing_count=34,
            missing_pct=0.0048,
            unique_count=1461,
            unique_pct=0.207,
            parse_rate=0.981,
        ),
        ColumnProfile(
            name="support_tickets",
            inferred_type=InferredType.NUMERIC_DISCRETE,
            pandas_dtype="int64",
            missing_count=0,
            missing_pct=0.0,
            unique_count=9,
            unique_pct=0.0013,
            top_value_pct=0.612,
            min=0.0,
            max=8.0,
            mean=0.734,
            std=1.284,
            median=0.0,
            target_association=0.271,
            association_method=AssociationMethod.ETA,
        ),
        ColumnProfile(
            name="internal_notes",
            inferred_type=InferredType.TEXT,
            pandas_dtype="object",
            missing_count=6702,
            missing_pct=0.9516,
            unique_count=338,
            unique_pct=0.048,
            flags=[ColumnFlag.HIGH_MISSING],
        ),
        ColumnProfile(
            name="churn_reason",
            inferred_type=InferredType.CATEGORICAL,
            pandas_dtype="object",
            missing_count=5174,
            missing_pct=0.7346,
            unique_count=5,
            unique_pct=0.0007,
            top_value_pct=0.331,
            sample_values=[
                "Competitor offer",
                "Price",
                "Service quality",
                "Moved",
                "Other",
            ],
            target_association=0.994,
            association_method=AssociationMethod.PURITY,
            flags=[ColumnFlag.HIGH_MISSING, ColumnFlag.POTENTIAL_LEAKAGE],
        ),
        ColumnProfile(
            name="churn",
            inferred_type=InferredType.CATEGORICAL,
            pandas_dtype="object",
            missing_count=0,
            missing_pct=0.0,
            unique_count=2,
            unique_pct=0.0003,
            top_value_pct=0.7346,
            sample_values=["No", "Yes"],
        ),
    ]


def profile_card(target_column: str) -> ProfileCard:
    """Screen 2 result.

    The requested target is echoed into the card so the selection made on
    screen 1.5 is reflected downstream. Every other number is fixed.
    """
    return ProfileCard(
        dataset_id=FIXTURE_DATASET_ID,
        filename=FIXTURE_FILENAME,
        n_rows=FIXTURE_ROWS,
        n_columns=len(FIXTURE_COLUMNS),
        target_column=target_column or FIXTURE_TARGET,
        problem_type=ProblemType.BINARY_CLASSIFICATION,
        task_confidence=0.94,
        # 5174 negatives to 1869 positives. Above BALANCE_ACCURACY_MAX and
        # below BALANCE_F1_MAX, so the middle band applies and the metric is F1.
        primary_metric=Metric.F1,
        # Shown alongside the primary so the choice can be checked rather than
        # taken on trust. roc_auc appears here and never as a primary.
        secondary_metrics=[Metric.ACCURACY, Metric.ROC_AUC, Metric.PR_AUC],
        class_balance_ratio=2.768,
        duplicate_row_count=0,
        profiled_on_sample=False,
        sample_rows=None,
        columns=_column_profiles(),
    )


GENERATED_CODE = '''"""Churn prediction pipeline.

Generated strategy. This code has not been executed.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "churn"
DROP = ["customer_id", "churn_reason", "internal_notes", "signup_date"]

df = pd.read_csv("data.csv", engine="c")

# total_charges arrives as text because blank strings appear for new accounts.
df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")

y = (df[TARGET] == "Yes").astype(int)
X = df.drop(columns=[TARGET, *DROP])

numeric = ["tenure_months", "monthly_charges", "total_charges", "support_tickets"]
categorical = ["gender", "contract_type"]
passthrough = ["senior_citizen"]

preprocess = ColumnTransformer(
    transformers=[
        (
            "num",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                ]
            ),
            numeric,
        ),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore", drop="if_binary"),
            categorical,
        ),
        ("pass", "passthrough", passthrough),
    ]
)

model = Pipeline(
    [
        ("preprocess", preprocess),
        (
            "clf",
            HistGradientBoostingClassifier(
                max_iter=300,
                learning_rate=0.06,
                class_weight="balanced",
                random_state=42,
            ),
        ),
    ]
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_f1 = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1")
print(f"cross-validated f1: {cv_f1.mean():.4f} (+/- {cv_f1.std():.4f})")

model.fit(X_train, y_train)
preds = model.predict(X_test)
print(f"holdout f1: {f1_score(y_test, preds):.4f}")
print(classification_report(y_test, preds, target_names=["retained", "churned"]))
'''


def gen_result(target_column: str) -> GenResult:
    """Screen 3 and 4 result."""
    return GenResult(
        problem_type=ProblemType.BINARY_CLASSIFICATION,
        target_column=target_column or FIXTURE_TARGET,
        primary_metric=Metric.F1,
        dropped_columns=[
            DroppedColumn(
                column="customer_id",
                reason="Unique for every row, so it carries no generalisable signal and "
                "would let a tree memorise the training set.",
            ),
            DroppedColumn(
                column="churn_reason",
                reason="Target leakage. It is populated only for customers who already "
                "churned, so it is recorded after the outcome it would predict.",
            ),
            DroppedColumn(
                column="internal_notes",
                reason="Missing in 95% of rows, and free text that would need its own "
                "representation to be usable at all.",
            ),
            DroppedColumn(
                column="signup_date",
                reason="Superseded by tenure_months, which encodes the same information "
                "as a duration rather than an absolute date that will not "
                "generalise past the training window.",
            ),
        ],
        preprocessing=[
            PreprocessingStep(
                step="numeric coercion",
                columns=["total_charges"],
                rationale="Stored as text because new accounts carry a blank string. "
                "Coerce with errors='coerce' so the blanks become NaN and are "
                "handled by the imputer rather than crashing the cast.",
            ),
            PreprocessingStep(
                step="median imputation",
                columns=[
                    "tenure_months",
                    "monthly_charges",
                    "total_charges",
                    "support_tickets",
                ],
                rationale="Median rather than mean, because total_charges is strongly "
                "right-skewed and a mean fill would drag the imputed rows "
                "toward high-value customers.",
            ),
            PreprocessingStep(
                step="standard scaling",
                columns=[
                    "tenure_months",
                    "monthly_charges",
                    "total_charges",
                    "support_tickets",
                ],
                rationale="Costs nothing for the tree model and is required if the "
                "logistic regression baseline is to be comparable.",
            ),
            PreprocessingStep(
                step="one-hot encoding",
                columns=["gender", "contract_type"],
                rationale="Both are nominal with three or fewer levels, so one-hot adds "
                "three columns in total. handle_unknown='ignore' keeps "
                "inference working on unseen levels.",
            ),
            PreprocessingStep(
                step="class weighting",
                columns=["churn"],
                rationale="A 2.77:1 imbalance is mild enough that resampling is not "
                "warranted, but balanced class weights stop the model from "
                "settling on the majority class.",
            ),
        ],
        candidate_models=[
            CandidateModel(
                name="HistGradientBoostingClassifier",
                library="scikit-learn",
                rationale="Strongest default on mixed tabular data of this size, handles "
                "the residual NaNs natively, and trains in seconds on 7,000 rows.",
            ),
            CandidateModel(
                name="LogisticRegression",
                library="scikit-learn",
                rationale="Interpretable baseline. Churn work usually needs a coefficient "
                "the business can argue with, and it establishes whether the "
                "boosting gain is real.",
            ),
            CandidateModel(
                name="RandomForestClassifier",
                library="scikit-learn",
                rationale="Robust to the skew in total_charges without scaling, and a "
                "useful cross-check on the boosting model's feature ordering.",
            ),
        ],
        validation_strategy="Stratified 5-fold cross-validation on an 80% training split, "
        "with the remaining 20% held out untouched. Stratification matters "
        "at 2.77:1: an unstratified fold can land with materially fewer "
        "positives and make the F1 estimate swing.",
        analysis_summary="7,043 rows and 12 columns predicting a binary churn label at a "
        "2.77:1 class ratio, which puts the primary metric at F1 rather "
        "than accuracy. Four columns are dropped, one of them for leakage: "
        "churn_reason is recorded only after a customer has churned and "
        "shows a 0.99 association with the target. total_charges needs "
        "coercion before use because blank strings for new accounts force "
        "it to text. The remaining seven features are a workable mix of "
        "tenure, billing, contract and support signal.",
        risks=[
            "churn_reason is a textbook leak. If it is left in, cross-validated F1 will "
            "look near-perfect and the model will be worthless in production.",
            "signup_date was dropped in favour of tenure_months. If churn is genuinely "
            "seasonal, that seasonality is now unavailable to the model.",
            "The 11 blank total_charges rows are all zero-tenure accounts, so imputing "
            "them to the median describes them as average-value customers, which is "
            "the opposite of what they are.",
            "No metric in this plan has been measured. The pipeline has not been run.",
        ],
        code=GENERATED_CODE,
    )


def validation_report() -> ValidationReport:
    """Screen 4 checklist.

    Deliberately not all green. A checklist that always passes teaches the user
    to stop reading it, and the frontend needs to render the failing state.
    """
    checks = [
        ValidationCheck(
            check_id="syntax_compile",
            title="Code compiles",
            severity=ValidationSeverity.ERROR,
            passed=True,
            message="Parsed by compile() without a SyntaxError.",
        ),
        ValidationCheck(
            check_id="ast_import_allowlist",
            title="Imports are allowlisted",
            severity=ValidationSeverity.ERROR,
            passed=True,
            message="All 4 imported modules are on the allowlist.",
            details=["pandas", "sklearn.compose", "sklearn.ensemble", "sklearn.pipeline"],
        ),
        ValidationCheck(
            check_id="dangerous_calls",
            title="No dangerous calls",
            severity=ValidationSeverity.ERROR,
            passed=True,
            message="No use of eval, exec, __import__, open in write mode, or subprocess.",
        ),
        ValidationCheck(
            check_id="hallucinated_columns",
            title="All referenced columns exist",
            severity=ValidationSeverity.ERROR,
            passed=True,
            message="Every column name in the code appears in the dataset.",
        ),
        ValidationCheck(
            check_id="target_not_in_features",
            title="Target excluded from features",
            severity=ValidationSeverity.ERROR,
            passed=True,
            message="churn is dropped from X before fitting.",
        ),
        ValidationCheck(
            check_id="drop_consistency",
            title="Declared drops match the code",
            severity=ValidationSeverity.WARNING,
            passed=True,
            message="All 4 columns listed in dropped_columns are dropped in the code.",
        ),
        ValidationCheck(
            check_id="csv_engine",
            title="CSV read uses the C engine",
            severity=ValidationSeverity.WARNING,
            passed=True,
            message="read_csv specifies engine='c'.",
        ),
        ValidationCheck(
            check_id="preprocessing_coverage",
            title="Every retained column is handled",
            severity=ValidationSeverity.WARNING,
            passed=False,
            message="1 retained column appears in no preprocessing step and is passed "
            "through unchanged. Intentional for a boolean flag, but confirm.",
            details=["senior_citizen"],
        ),
        ValidationCheck(
            check_id="random_seed",
            title="Run is reproducible",
            severity=ValidationSeverity.INFO,
            passed=True,
            message="random_state is set on the split, the folds, and the estimator.",
        ),
    ]
    errors = sum(1 for c in checks if not c.passed and c.severity is ValidationSeverity.ERROR)
    warnings = sum(1 for c in checks if not c.passed and c.severity is ValidationSeverity.WARNING)
    return ValidationReport(
        passed=errors == 0,
        error_count=errors,
        warning_count=warnings,
        checks=checks,
    )
