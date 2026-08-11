/**
 * Section 25: "one of the most visually important components." The
 * rationale text below is generated here, in the frontend, from real
 * ProfileCard fields (problem_type, primary_metric, class_balance_ratio) -
 * there is no rationale string anywhere in the API. Every number quoted is
 * the real class_balance_ratio, never a hardcoded copy of the backend's
 * band thresholds (BALANCE_ACCURACY_MAX, BALANCE_F1_MAX in heuristics.py),
 * so this stays correct even if those constants are retuned later.
 *
 * Section 25 again: never "AI recommends X" - this is a deterministic
 * function of the profile, attributed to dataset analysis, not a model.
 */

import type { Metric, ProblemType } from "../../types";

const METRIC_LABEL: Record<Metric, string> = {
  accuracy: "Accuracy",
  f1: "F1 Score",
  f1_macro: "F1 Score (macro)",
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  rmse: "RMSE",
  mae: "MAE",
  r2: "R²",
};

function rationale(problemType: ProblemType, metric: Metric, ratio: number | null): string {
  if (problemType === "regression") {
    return "This target is continuous, so RMSE reports prediction error in the target's own units.";
  }
  if (problemType === "multiclass_classification") {
    return "This target has more than two classes, so the primary metric averages performance across every class equally rather than using a measure defined only for two.";
  }
  const ratioText = ratio !== null ? `about ${ratio.toFixed(2)}:1` : "an unknown ratio";
  if (metric === "accuracy") {
    return `The classes are close to balanced (${ratioText}), so accuracy reflects real performance without a majority-class shortcut inflating it.`;
  }
  if (metric === "f1") {
    return `The classes are imbalanced (${ratioText}). F1 balances precision and recall, rather than rewarding a model that mostly predicts the majority class.`;
  }
  return `The classes are heavily imbalanced (${ratioText}). PR-AUC stays informative across decision thresholds, where accuracy or F1 would be dominated by the majority class.`;
}

export function MetricPanel({
  problemType,
  primaryMetric,
  secondaryMetrics,
  classBalanceRatio,
}: {
  problemType: ProblemType;
  primaryMetric: Metric;
  secondaryMetrics: Metric[];
  classBalanceRatio: number | null;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <p className="text-caption font-caption uppercase tracking-wide text-text-tertiary">
        Recommended by dataset analysis
      </p>
      <p className="mt-2 text-display font-display text-text-primary">
        {METRIC_LABEL[primaryMetric]}
      </p>
      <p className="mt-3 max-w-[var(--prose-max-width)] text-secondary-size leading-relaxed text-text-secondary">
        {rationale(problemType, primaryMetric, classBalanceRatio)}
      </p>
      {secondaryMetrics.length > 0 ? (
        <p className="mt-4 text-caption text-text-tertiary">
          Also reported: {secondaryMetrics.map((metric) => METRIC_LABEL[metric]).join(", ")}
        </p>
      ) : null}
    </div>
  );
}
