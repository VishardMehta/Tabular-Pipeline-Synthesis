"""Class balance and primary/secondary metric selection.

Not prompt surface.

This module is the implementation of the tables in heuristics.md. It makes no
decisions of its own; every threshold it reads is named in heuristics.py.
"""

from __future__ import annotations

import pandas as pd

from app import heuristics
from app.models import Metric, ProblemType


def class_balance_ratio(y: pd.Series, problem_type: ProblemType) -> float | None:
    """Most frequent class count over least frequent. None for regression.

    heuristics.md gives the binary definition as n_majority / n_minority. This
    is the same ratio, generalized past two classes the same way "majority"
    and "minority" generalize on their own: whichever class is most and least
    frequent, regardless of count. heuristics.md is explicit that multiclass
    does not read this value against the bands (f1_macro is fixed regardless
    of ratio), so the generalization changes no metric decision. It exists so
    ProfileCard.class_balance_ratio reports a consistent number across problem
    types rather than being None for multiclass for no principled reason.

    An alternative, (1 / n_classes) / min_class_proportion, was proposed and
    rejected. It was meant to generalize past binary without leaning on
    "majority" and "minority", but that problem does not need solving here:
    multiclass never reads this value against the bands at all, so there was
    nothing to generalize for. The two formulas also disagree numerically at
    every imbalance away from an even split - 9.0 versus 5.0 at a 90/10
    split - and n_majority / n_minority is what BALANCE_ACCURACY_MAX and
    BALANCE_F1_MAX were calibrated against, so it is the one that keeps the
    bands meaning what their comments say they mean.
    """
    if problem_type is ProblemType.REGRESSION:
        return None
    counts = y.dropna().value_counts()
    if len(counts) < 2:
        return None
    return float(counts.max() / counts.min())


def select_metrics(
    problem_type: ProblemType, class_balance_ratio: float | None
) -> tuple[Metric, list[Metric]]:
    """Primary and secondary metrics, per the tables in heuristics.md.

    Regression: RMSE always primary. MAE and R2 always secondary, never
    primary - see TARGET_SKEW_THRESHOLD's comment for why the primary does not
    switch to MAE on a heavy-tailed target.

    Multiclass: f1_macro always primary, accuracy secondary. The bands on
    class_balance_ratio are not read - a fifteen-class dataset can show a wide
    spread between its largest and smallest class while being entirely
    reasonable to model, and pr_auc has no agreed definition for multiclass.

    Binary: class_balance_ratio against the three bands chooses the primary.
    The two bands not chosen become secondaries, plus roc_auc, which no band
    ever selects because it stays flattering under imbalance while precision
    collapses.

    Every path returns secondaries. Suppressing the alternatives is the
    black-box behaviour this tool argues against - a primary metric shown
    alone cannot be checked for whether it was chosen to flatter the result.
    """
    if problem_type is ProblemType.REGRESSION:
        return Metric.RMSE, [Metric.MAE, Metric.R2]

    if problem_type is ProblemType.MULTICLASS_CLASSIFICATION:
        return Metric.F1_MACRO, [Metric.ACCURACY]

    # Binary. TARGET_SINGLE_VALUE is raised before this is reachable, so a
    # binary target always has an observed ratio here.
    if class_balance_ratio is None:
        raise ValueError("binary target must have a class balance ratio")

    if class_balance_ratio <= heuristics.BALANCE_ACCURACY_MAX:
        primary = Metric.ACCURACY
    elif class_balance_ratio <= heuristics.BALANCE_F1_MAX:
        primary = Metric.F1
    else:
        primary = Metric.PR_AUC

    bands = (Metric.ACCURACY, Metric.F1, Metric.PR_AUC)
    secondary = [metric for metric in bands if metric is not primary]
    secondary.append(Metric.ROC_AUC)
    return primary, secondary
