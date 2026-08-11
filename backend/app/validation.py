"""Static validation of a generated GenResult against the ProfileCard it was
generated from.

Not prompt surface - nothing here is sent to the model. The messages are
still written for the person deciding whether to trust the pipeline, though,
so they follow the same rule as prompts.py: say what the code did and what a
passing version looks like, not only that a check failed. See CLAUDE.md,
"Prompt authoring: say Y, never write 'never X' alone" - the same finding
applies to a validator's failure text as much as to a system prompt.

Nothing here executes the generated code. Every check is compile(), ast, or a
string/set comparison against facts already in GenResult and ProfileCard.
"""

from __future__ import annotations

import ast
import difflib

from app import heuristics
from app.models import (
    GenResult,
    Metric,
    ProfileCard,
    ValidationCheck,
    ValidationReport,
    ValidationSeverity,
)

# ---------------------------------------------------------------------------
# Import allowlist and dangerous calls
# ---------------------------------------------------------------------------

# Exactly the three libraries _CODE_CONSTRAINTS in prompts.py tells the model
# it may import. A rule this check enforces but the prompt never states would
# be marking against an unstated exam - see test_prompts.py for the same
# principle applied to the prompt itself.
_ALLOWED_IMPORT_ROOTS = {"pandas", "numpy", "sklearn"}

# Bare builtins that need no import to be dangerous.
_DANGEROUS_BUILTINS = {"eval", "exec", "compile", "__import__"}
# Modules whose entire call surface is dangerous. Not "os" wholesale - os.path
# and os.environ are ordinary, and only os.system executes a shell - so os
# gets one specific dotted name instead of a blanket module ban.
_DANGEROUS_MODULE_ROOTS = {"subprocess", "socket", "requests", "urllib"}
_DANGEROUS_DOTTED = {"os.system"}


def _dotted_call_name(func: ast.expr) -> str | None:
    """Reconstruct "a.b.c" for a Name or Attribute call target.

    Returns None for anything more dynamic - a call on a subscript, a call
    result, getattr() - that static analysis does not attempt to resolve.
    That is a real blind spot, not an oversight: `getattr(__builtins__,
    "eval")(...)` evades this the same way it would evade any static check.
    """
    parts: list[str] = []
    node = func
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        parts.reverse()
        return ".".join(parts)
    return None


def _imported_roots(tree: ast.AST) -> list[tuple[str, int]]:
    """Every top-level module name a statement imports, paired with its
    line number for the check's details."""
    roots: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append((alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append((node.module.split(".")[0], node.lineno))
    return roots


def _check_import_allowlist(tree: ast.AST) -> ValidationCheck:
    offending_roots = {
        root for root, _ in _imported_roots(tree) if root not in _ALLOWED_IMPORT_ROOTS
    }
    details = sorted(
        f"{root} (line {lineno})"
        for root, lineno in _imported_roots(tree)
        if root in offending_roots
    )
    passed = not offending_roots
    message = (
        "Every import resolves to pandas, numpy or scikit-learn, the only "
        "libraries available where this code runs."
        if passed
        else "These imports are outside pandas, numpy and scikit-learn, the only "
        f"libraries available where this code runs: {', '.join(sorted(offending_roots))}."
    )
    return ValidationCheck(
        check_id="ast_import_allowlist",
        title="Imports are allowlisted",
        severity=ValidationSeverity.ERROR,
        passed=passed,
        message=message,
        details=details,
    )


def _check_dangerous_calls(tree: ast.AST) -> ValidationCheck:
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted_call_name(node.func)
        if dotted is None:
            continue
        root = dotted.split(".")[0]
        is_dangerous = (
            dotted in _DANGEROUS_BUILTINS
            or dotted in _DANGEROUS_DOTTED
            or root in _DANGEROUS_MODULE_ROOTS
        )
        if is_dangerous:
            offenders.append(f"{dotted}() at line {node.lineno}")
    passed = not offenders
    message = (
        "No use of eval, exec, compile, __import__, os.system, subprocess, "
        "socket, requests or urllib."
        if passed
        else "These calls can read, write or reach outside data.csv, which this "
        "code is not permitted to do: " + ", ".join(offenders)
    )
    return ValidationCheck(
        check_id="dangerous_calls",
        title="No dangerous calls",
        severity=ValidationSeverity.ERROR,
        passed=passed,
        message=message,
        details=offenders,
    )


# ---------------------------------------------------------------------------
# Column literal extraction
#
# Shared with tests/test_llm.py's cassette checks - moved here so there is
# one implementation, not two that can quietly drift apart.
# ---------------------------------------------------------------------------

# Names of variables that plausibly hold a list of column names, checked
# case-insensitively. Measured against three real generations in stage 3:
# every one of them names its feature columns exactly this way (a DROP list,
# or a numeric_features / categorical style list), never as bare df["x"]
# literals scattered through the body.
COLUMN_LIST_VARS = {
    "drop",
    "numeric_features",
    "numeric",
    "categorical_features",
    "categorical",
    "features",
    "columns",
    "passthrough",
}

# Sklearn parameter values and file paths that can land in the same AST
# shapes a real column reference would, but are not column names. Short
# rather than exhaustive: the collector below is already scoped to subscript
# keys and named column-list variables, so most parameter values never reach
# either shape to begin with.
_KNOWN_NON_COLUMN_LITERALS = {
    "data.csv",
    "mean",
    "median",
    "most_frequent",
    "constant",
    "ignore",
    "error",
    "first",
    "if_binary",
    "auto",
}


def referenced_column_literals(tree: ast.AST) -> set[str]:
    """String literals the code treats as column names.

    Two shapes, both measured against real generations rather than assumed:
    a subscript key (df["x"], X["x"]) and a list literal assigned to a
    variable named like the ones in COLUMN_LIST_VARS (DROP = [...],
    numeric_features = [...]). Not a full data-flow analysis - a Name used
    as a subscript key (df[TARGET]) is deliberately skipped, since TARGET is
    a variable, not a literal, and resolving it would mean tracking
    assignment across the whole function for no real gain: the target is
    checked separately, by target_column_referenced.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            names.add(node.slice.value)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.lower() in COLUMN_LIST_VARS:
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        names.add(elt.value)
    return names - _KNOWN_NON_COLUMN_LITERALS


# Of COLUMN_LIST_VARS, the subset that names an exclusion list rather than a
# feature list. A column appearing only inside DROP = [...] is being
# declared dropped, not used - the opposite of what dropped_columns_not_
# referenced needs to detect, so that check reads feature_usage_literals
# below instead of referenced_column_literals.
_DROP_LIST_VARS = {"drop", "dropped", "excluded", "exclude"}


def feature_usage_literals(tree: ast.AST) -> set[str]:
    """Column literals with real evidence of feature use: a subscript read
    (df["x"], X["x"]) or membership in a column-list variable that is not
    itself a drop list.

    Narrower than referenced_column_literals on purpose. That function is
    right for hallucination detection, where a typo inside DROP = [...] is
    still worth flagging. It is wrong for "is a dropped column still used as
    a feature", where DROP = [...] is precisely the declaration that a
    column is excluded, not evidence it survived into the feature matrix.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
            and not isinstance(node.ctx, ast.Store)
        ):
            names.add(node.slice.value)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            target = node.targets[0]
            is_feature_list = (
                isinstance(target, ast.Name)
                and target.id.lower() in COLUMN_LIST_VARS
                and target.id.lower() not in _DROP_LIST_VARS
            )
            if is_feature_list:
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        names.add(elt.value)
    return names - _KNOWN_NON_COLUMN_LITERALS


def defined_column_literals(tree: ast.AST) -> set[str]:
    """Column names the code creates itself: df["new_col"] = ....

    Never a hallucination. The spike behind this project (see
    docs/spike-01-gemini-structured-output.md) found two of nine live
    generations engineered a feature this way, and a check that does not
    know about self-defined columns reports every one of them as a
    hallucinated reference to a column that does not exist.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.slice, ast.Constant)
                and isinstance(target.slice.value, str)
            ):
                names.add(target.slice.value)
    return names


def _all_string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _check_hallucinated_columns(tree: ast.AST, profile: ProfileCard) -> ValidationCheck:
    """Flags near-misses only - a literal within SIMILARITY_CUTOFF of a real
    column but not equal to one - not every unrecognised string. A stricter
    "flag anything not a known or self-defined column" check would also catch
    every legitimate engineered feature and every sklearn parameter this
    collector's scoping happens not to exclude, training the user to ignore
    the check the same way the "always green" checklist in the old stage 0
    fixture was deliberately avoided.
    """
    known = {column.name for column in profile.columns}
    candidates = referenced_column_literals(tree) - known - defined_column_literals(tree)

    offenders: list[str] = []
    for literal in sorted(candidates):
        best = max(known, key=lambda name: difflib.SequenceMatcher(None, literal, name).ratio())
        ratio = difflib.SequenceMatcher(None, literal, best).ratio()
        if ratio >= heuristics.SIMILARITY_CUTOFF:
            offenders.append(f"'{literal}' is not a column, but is close to '{best}' - a typo?")

    passed = not offenders
    message = (
        "Every column-shaped string literal is a real column or one the code "
        "defines itself."
        if passed
        else "One or more referenced names are near-misses of a real column - "
        "the profile of a typo, not an engineered feature: " + " ".join(offenders)
    )
    return ValidationCheck(
        check_id="hallucinated_columns",
        title="No near-miss column names",
        severity=ValidationSeverity.ERROR,
        passed=passed,
        message=message,
        details=offenders,
    )


def _check_target_referenced(tree: ast.AST, target_column: str) -> ValidationCheck:
    passed = target_column in _all_string_constants(tree)
    message = (
        f"'{target_column}' appears in the code, so the target the strategy "
        "names is the target the code actually trains against."
        if passed
        else f"'{target_column}' never appears anywhere in the code. A pipeline "
        "that never references its target cannot be training against it."
    )
    return ValidationCheck(
        check_id="target_column_referenced",
        title="Target column is used",
        severity=ValidationSeverity.ERROR,
        passed=passed,
        message=message,
    )


def _check_self_consistency(result: GenResult, profile: ProfileCard) -> ValidationCheck:
    """The three fields _FACTS_ARE_AUTHORITATIVE in prompts.py tells the
    model to restate exactly, not re-decide. A mismatch here means the
    response overrode a fact the profile had already settled."""
    mismatches: list[str] = []
    if result.problem_type != profile.problem_type:
        mismatches.append(
            f"problem_type: result says {result.problem_type.value}, profile "
            f"says {profile.problem_type.value}."
        )
    if result.target_column != profile.target_column:
        mismatches.append(
            f"target_column: result says '{result.target_column}', profile "
            f"says '{profile.target_column}'."
        )
    if result.primary_metric != profile.primary_metric:
        mismatches.append(
            f"primary_metric: result says {result.primary_metric.value}, "
            f"profile says {profile.primary_metric.value}."
        )
    passed = not mismatches
    message = (
        "problem_type, target_column and primary_metric all match the profile, "
        "exactly as the prompt asked the model to restate them."
        if passed
        else "The result changed a fact the profile had already settled instead "
        "of restating it. A correct response copies these three fields exactly: "
        + " ".join(mismatches)
    )
    return ValidationCheck(
        check_id="gen_result_self_consistency",
        title="Result matches the profile's own decisions",
        severity=ValidationSeverity.ERROR,
        passed=passed,
        message=message,
        details=mismatches,
    )


# ---------------------------------------------------------------------------
# Structural warnings
# ---------------------------------------------------------------------------


def _call_names(tree: ast.AST) -> set[str]:
    """The bare name or final attribute of every call in the code -
    "Pipeline" from Pipeline(...) and "ColumnTransformer" from
    ct.ColumnTransformer(...) alike. Enough for "was this constructed
    anywhere", which is all four of the WARN checks below ask."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _check_pipeline_or_column_transformer(tree: ast.AST) -> ValidationCheck:
    passed = bool(_call_names(tree) & {"Pipeline", "ColumnTransformer"})
    message = (
        "The code builds a Pipeline or ColumnTransformer, so preprocessing "
        "and the estimator travel together."
        if passed
        else "No Pipeline or ColumnTransformer is constructed anywhere. "
        "Preprocessing applied by hand outside one is easy to apply "
        "differently between training and held-out evaluation."
    )
    return ValidationCheck(
        check_id="pipeline_or_column_transformer",
        title="Uses a Pipeline or ColumnTransformer",
        severity=ValidationSeverity.WARNING,
        passed=passed,
        message=message,
    )


def _check_random_state(tree: ast.AST) -> ValidationCheck:
    """_CODE_CONSTRAINTS #6 in prompts.py says "set random_state on every
    split, fold and estimator" - a presence rule, not a specific value. It
    never asks for 42 anywhere; the worked example's own closing line says
    its choices "belong to that dataset. Yours will differ." Requiring 42
    specifically would mark against a rule the prompt never states - the
    same unstated-exam trap test_prompts.py already guards the prompt
    against, applied here to the validator instead.
    """
    found = any(
        isinstance(node, ast.keyword) and node.arg == "random_state" for node in ast.walk(tree)
    )
    message = (
        "random_state is set at least once."
        if found
        else "random_state does not appear anywhere. Without it, the split, the "
        "folds or the estimator can give a different answer on every run, and "
        "the result cannot be reproduced by the person reading it."
    )
    return ValidationCheck(
        check_id="random_state_set",
        title="Reproducible with random_state",
        severity=ValidationSeverity.WARNING,
        passed=found,
        message=message,
    )


_SPLIT_OR_CV_CALLS = {
    "train_test_split",
    "KFold",
    "StratifiedKFold",
    "cross_val_score",
    "cross_validate",
    "GridSearchCV",
    "RandomizedSearchCV",
    "TimeSeriesSplit",
    "RepeatedKFold",
    "RepeatedStratifiedKFold",
    "ShuffleSplit",
    "StratifiedShuffleSplit",
}


def _check_split_or_cv(tree: ast.AST) -> ValidationCheck:
    passed = bool(_call_names(tree) & _SPLIT_OR_CV_CALLS)
    message = (
        "The code holds out data for evaluation, by a train/test split or "
        "cross-validation."
        if passed
        else "No train/test split and no cross-validation call appears anywhere. "
        "Any metric this code prints would be measured on the data it trained on."
    )
    return ValidationCheck(
        check_id="split_or_cross_validation",
        title="Evaluates on held-out data",
        severity=ValidationSeverity.WARNING,
        passed=passed,
        message=message,
    )


# Substrings that indicate a metric was actually computed, not just named in
# a comment. String search over the source rather than another AST walk -
# these can appear as a scoring= string, a function call, or an average=
# keyword, and matching the source text catches all three without writing a
# separate AST shape for each.
_METRIC_KEYWORDS: dict[Metric, tuple[str, ...]] = {
    Metric.ACCURACY: ("accuracy_score", '"accuracy"', "'accuracy'"),
    Metric.F1: ("f1_score", '"f1"', "'f1'"),
    Metric.F1_MACRO: ("f1_score", '"f1_macro"', "'f1_macro'", 'average="macro"', "average='macro'"),
    Metric.PR_AUC: (
        "average_precision_score",
        "precision_recall_curve",
        '"average_precision"',
        "'average_precision'",
    ),
    Metric.ROC_AUC: ("roc_auc_score", '"roc_auc"', "'roc_auc'"),
    Metric.RMSE: ("root_mean_squared_error", "neg_root_mean_squared_error", "mean_squared_error"),
    Metric.MAE: ("mean_absolute_error", "neg_mean_absolute_error"),
    Metric.R2: ("r2_score", '"r2"', "'r2'"),
}


def _check_primary_metric_computed(code: str, primary_metric: Metric) -> ValidationCheck:
    passed = any(keyword in code for keyword in _METRIC_KEYWORDS[primary_metric])
    message = (
        f"The code computes {primary_metric.value}, the metric the profile "
        "names as primary."
        if passed
        else f"{primary_metric.value} is the primary metric, but nothing in the "
        "code appears to compute it - there is no number to check the strategy against."
    )
    return ValidationCheck(
        check_id="primary_metric_computed",
        title="Primary metric is actually computed",
        severity=ValidationSeverity.WARNING,
        passed=passed,
        message=message,
    )


def _check_declared_columns_exist(result: GenResult, profile: ProfileCard) -> ValidationCheck:
    known = {column.name for column in profile.columns}
    offenders: list[str] = []
    for dropped in result.dropped_columns:
        if dropped.column not in known:
            offenders.append(f"dropped_columns: '{dropped.column}'")
    for step in result.preprocessing:
        for column in step.columns:
            if column not in known:
                offenders.append(f"preprocessing ({step.step}): '{column}'")
    passed = not offenders
    message = (
        "Every column named in dropped_columns and preprocessing exists in "
        "the profile."
        if passed
        else "These declared columns do not appear in the profile at all, so "
        "the strategy describes a dataset that is not the one profiled: "
        + "; ".join(offenders)
    )
    return ValidationCheck(
        check_id="declared_columns_exist",
        title="Declared columns exist in the profile",
        severity=ValidationSeverity.WARNING,
        passed=passed,
        message=message,
        details=offenders,
    )


def _check_dropped_columns_not_referenced(tree: ast.AST, result: GenResult) -> ValidationCheck:
    """Not in the enumerated FAIL/WARN list for this stage, added because the
    fixture corpus explicitly asks for "a reference to a dropped column" and
    no other check covers it - declared_columns_exist checks the opposite
    direction (do the declared names exist in the profile), not whether the
    code actually leaves them out. Same family, same severity, the missing
    half of the same consistency question. Flagged here rather than silently
    folded in, and called out again in the stage 4 report.
    """
    used = feature_usage_literals(tree)
    dropped = {column.column for column in result.dropped_columns}
    offenders = sorted(used & dropped)
    passed = not offenders
    message = (
        "None of the columns declared dropped are referenced in the code."
        if passed
        else "The strategy declares these columns dropped, but the code still "
        "references them as features: " + ", ".join(offenders)
    )
    return ValidationCheck(
        check_id="dropped_columns_not_referenced",
        title="Dropped columns stay dropped",
        severity=ValidationSeverity.WARNING,
        passed=passed,
        message=message,
        details=offenders,
    )


# ---------------------------------------------------------------------------
# Syntax and entry point
# ---------------------------------------------------------------------------


def _check_syntax(code: str) -> tuple[ValidationCheck, ast.Module | None]:
    try:
        compile(code, "<generated>", "exec")
        tree = ast.parse(code)
    except (SyntaxError, ValueError) as exc:
        check = ValidationCheck(
            check_id="syntax_compile",
            title="Code compiles",
            severity=ValidationSeverity.ERROR,
            passed=False,
            message=f"The code does not parse as Python: {exc}.",
            details=[f"line {getattr(exc, 'lineno', '?')}"],
        )
        return check, None
    check = ValidationCheck(
        check_id="syntax_compile",
        title="Code compiles",
        severity=ValidationSeverity.ERROR,
        passed=True,
        message="Parsed by compile() without a SyntaxError.",
    )
    return check, tree


def validate(result: GenResult, profile: ProfileCard) -> ValidationReport:
    """Every static check this stage defines, in the order specified.

    When the code fails to parse, every check that needs an AST is left out
    of the report entirely rather than reported as passed or failed - both
    would assert something never actually tested. Only the two checks that
    read GenResult and ProfileCard directly, not the code, still run.
    """
    checks: list[ValidationCheck] = []

    syntax_check, tree = _check_syntax(result.code)
    checks.append(syntax_check)

    if tree is not None:
        checks.append(_check_import_allowlist(tree))
        checks.append(_check_dangerous_calls(tree))
        checks.append(_check_hallucinated_columns(tree, profile))
        checks.append(_check_target_referenced(tree, profile.target_column))

    checks.append(_check_self_consistency(result, profile))

    if tree is not None:
        checks.append(_check_pipeline_or_column_transformer(tree))
        checks.append(_check_random_state(tree))
        checks.append(_check_split_or_cv(tree))
        checks.append(_check_primary_metric_computed(result.code, profile.primary_metric))

    checks.append(_check_declared_columns_exist(result, profile))

    if tree is not None:
        checks.append(_check_dropped_columns_not_referenced(tree, result))

    errors = sum(1 for c in checks if not c.passed and c.severity is ValidationSeverity.ERROR)
    warnings = sum(1 for c in checks if not c.passed and c.severity is ValidationSeverity.WARNING)
    return ValidationReport(
        passed=errors == 0,
        error_count=errors,
        warning_count=warnings,
        checks=checks,
    )
