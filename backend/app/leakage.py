"""How strongly one feature associates with the target.

Not prompt surface.

Three formulas cover every practical combination of feature and target type,
chosen so nothing beyond pandas and numpy is needed:

  numeric feature,     regression target     -> Spearman rank correlation
  numeric feature,     classification target -> correlation ratio (eta)
  categorical feature, classification target -> a purity measure
  categorical feature, regression target     -> correlation ratio (eta),
                                                 with the two series' roles
                                                 swapped from the case above

heuristics.md and the target_association docstring in models.py specify
Spearman for a numeric feature against a regression target, and point-biserial
for a numeric feature against a binary target, but leave categorical features
and multiclass targets undefined. Point-biserial is the two-group special case
of the correlation ratio: eta reduces algebraically to |Pearson r| when there
are exactly two groups. Using eta for every "numeric feature vs classification
target" pairing satisfies the point-biserial requirement on binary targets
while covering multiclass with the same formula rather than a second one.

The purity measure is this module's own construction. heuristics.md names the
concept, "level-to-class purity", without defining it, so a formula had to be
chosen rather than found; see purity()'s docstring for what it is and why.
This is called out as a decision in the stage 2 report, not presented as
something heuristics.md already specified.

Every function returns an association in [0, 1] with the sign already
discarded, consistent with LEAKAGE_R being defined as an absolute value. The
caller is responsible for sample-bounding large inputs before calling these;
none of them sample internally.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def spearman(feature: pd.Series, target: pd.Series) -> float | None:
    """Rank correlation between two numeric series.

    Rank rather than Pearson because it is monotonic rather than linear and
    survives a transform like a log scale on one side, which is exactly the
    kind of relationship a leaked-but-rescaled column would show.

    Computed by hand as the Pearson correlation of the two series' ranks,
    rather than via pandas' own method="spearman", because that path imports
    scipy internally and scipy is not a dependency this project carries.
    Ranking then correlating is the textbook definition of Spearman's rho, not
    an approximation of it.
    """
    paired = pd.DataFrame({"f": feature, "t": target}).dropna()
    if len(paired) < 2 or paired["f"].nunique() < 2 or paired["t"].nunique() < 2:
        return None
    ranked = paired.rank()
    rho = ranked["f"].corr(ranked["t"])
    return None if pd.isna(rho) else abs(float(rho))


def correlation_ratio(numeric: pd.Series, groups: pd.Series) -> float | None:
    """Eta: the share of the numeric series' variance explained by group
    membership.

    With exactly two groups this is |Pearson r| between the numeric series and
    a 0/1 encoding of the group, which is the definition of point-biserial
    correlation. With more than two groups it is the natural generalization,
    which is why one function covers a numeric feature against a binary
    target, a numeric feature against a multiclass target, and, with the two
    series swapped, a categorical feature against a regression target.
    """
    paired = pd.DataFrame({"value": numeric, "group": groups}).dropna()
    if len(paired) < 2 or paired["group"].nunique() < 2:
        return None

    grand_mean = paired["value"].mean()
    total_ss = float(((paired["value"] - grand_mean) ** 2).sum())
    if total_ss == 0:
        return None

    def group_ss(values: pd.Series) -> float:
        return len(values) * (values.mean() - grand_mean) ** 2

    between_ss = float(paired.groupby("group")["value"].apply(group_ss).sum())
    eta_squared = max(0.0, min(1.0, between_ss / total_ss))
    return float(np.sqrt(eta_squared))


def purity(categories: pd.Series, classes: pd.Series) -> float | None:
    """How much better than guessing the majority class does knowing the
    category get you.

    For each level of `categories`, take the share held by that level's single
    most common class, then average those shares weighted by how many rows
    carry the level. A category unrelated to the class reproduces roughly the
    same majority-class share every level would show by chance; one that
    perfectly separates classes drives every level's share to 1.0.

    Normalized against the baseline, the majority-class share with no
    information at all, so an uninformative category scores 0 rather than
    whatever the baseline happens to be:

        association = (weighted_purity - baseline) / (1 - baseline)

    Not a standard named statistic, unlike the other two functions here.
    heuristics.md names the concept without a formula, and this is the
    concrete choice made to implement it, favouring something that needs no
    dependency beyond pandas and lands on the same 0-1 scale as spearman() and
    correlation_ratio() over reaching for an established but heavier measure
    like Cramer's V, which would need scipy.
    """
    paired = pd.DataFrame({"cat": categories, "cls": classes}).dropna()
    if len(paired) < 2 or paired["cls"].nunique() < 2:
        return None

    baseline = float(paired["cls"].value_counts(normalize=True).max())
    if baseline >= 1.0:
        return None

    def level_share(values: pd.Series) -> float:
        return float(values.value_counts(normalize=True).max())

    level_counts = paired.groupby("cat")["cls"].size()
    level_shares = paired.groupby("cat")["cls"].apply(level_share)
    weighted_purity = float((level_counts * level_shares).sum() / len(paired))

    association = (weighted_purity - baseline) / (1 - baseline)
    return float(max(0.0, min(1.0, association)))
