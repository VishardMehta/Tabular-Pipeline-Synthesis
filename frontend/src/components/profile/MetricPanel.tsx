/**
 * The metric recommendation - one of the most visually important components
 * on the Profile screen, and the one place the design system spends a solid
 * blue field rather than a hairline-bordered white card. That weight is
 * earned: it is the single decision the rest of the pipeline is built
 * around.
 *
 * The rationale text is generated here, in the frontend, from real
 * ProfileCard fields (problem_type, primary_metric, class_balance_ratio) -
 * there is no rationale string anywhere in the API. Every number quoted is
 * the real class_balance_ratio, never a hardcoded copy of the backend's band
 * thresholds (BALANCE_ACCURACY_MAX, BALANCE_F1_MAX in heuristics.py), so
 * this stays correct if those constants are retuned later.
 *
 * Never "AI recommends X": this is a deterministic function of the profile,
 * attributed to dataset analysis, not to a model. And the rationale is
 * always on screen - never behind a tooltip.
 */

import { SparkleIcon } from "../shared/icons";
import type { Metric, ProblemType } from "../../types";

const METRIC_LABEL: Record<Metric, string> = {
  accuracy: "Accuracy",
  f1: "F1 Score",
  f1_macro: "F1 Macro",
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  rmse: "RMSE",
  mae: "MAE",
  r2: "R²",
};

function rationale(problemType: ProblemType, metric: Metric, ratio: number | null): string {
  if (problemType === "regression") {
    return "This target is continuous, so the primary metric reports prediction error in the target's own units.";
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
    // No h-full: the panel sizes to its own content. Matching the height of
    // whatever happens to sit beside it leaves a large empty blue field, which
    // reads as a rendering fault rather than as emphasis.
    <section className="rounded-lg bg-accent p-6 text-white">
      <p className="label-caps flex items-center gap-2 text-white/75">
        <SparkleIcon className="size-4" />
        Recommended by dataset analysis
      </p>

      <h2 className="mt-5 text-heading font-heading text-white/85">Optimizing for</h2>
      <p className="mt-1 font-mono text-[2.5rem] font-bold leading-tight tracking-tight">
        {METRIC_LABEL[primaryMetric]}
      </p>

      <p className="mt-4 text-secondary-size leading-relaxed text-white/90">
        {rationale(problemType, primaryMetric, classBalanceRatio)}
      </p>

      {secondaryMetrics.length > 0 ? (
        <div className="mt-6 border-t border-white/25 pt-4">
          <p className="label-caps mb-2 text-white/75">Also reported</p>
          <div className="flex flex-wrap gap-1.5">
            {secondaryMetrics.map((metric) => (
              <span
                key={metric}
                className="rounded-tag bg-white/15 px-2 py-1 font-mono text-data-sm text-white"
              >
                {METRIC_LABEL[metric]}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
