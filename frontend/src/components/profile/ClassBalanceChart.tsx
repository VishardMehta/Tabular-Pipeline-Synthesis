/**
 * Section 41: a horizontal bar chart, minimal and data-first, no legend and
 * no decoration beyond the label and the percentage.
 *
 * Real per-class labels only exist for binary classification: the target's
 * own ColumnProfile.sample_values, when populated, lists level names
 * ordered by descending frequency (profiler.py builds it from
 * value_counts().head()), so sample_values[0] is genuinely the majority
 * label and sample_values[1] the minority - not a guess. class_balance_ratio
 * (n_majority / n_minority) then gives the exact split via
 * ratio / (1 + ratio) and 1 / (1 + ratio). For multiclass, a single ratio
 * cannot be attributed to specific class names without inventing which
 * classes those are, so this falls back to an unlabeled ratio rather than
 * naming classes the profile never named.
 */

import type { ColumnProfile, ProblemType } from "../../types";

function Bar({ label, share, emphasis }: { label: string; share: number; emphasis: boolean }) {
  const pct = share * 100;
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 shrink-0 truncate text-secondary-size text-text-secondary" title={label}>
        {label}
      </span>
      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-secondary">
        <div
          className={`h-full rounded-full ${emphasis ? "bg-accent" : "bg-text-tertiary"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-12 shrink-0 text-right font-mono text-secondary-size text-text-primary">
        {pct.toFixed(pct < 10 ? 1 : 0)}%
      </span>
    </div>
  );
}

export function ClassBalanceChart({
  problemType,
  classBalanceRatio,
  targetColumn,
}: {
  problemType: ProblemType;
  classBalanceRatio: number | null;
  targetColumn: ColumnProfile | undefined;
}) {
  if (problemType === "regression" || classBalanceRatio === null) return null;

  const majorityShare = classBalanceRatio / (1 + classBalanceRatio);
  const minorityShare = 1 / (1 + classBalanceRatio);

  const hasRealLabels =
    problemType === "binary_classification" &&
    targetColumn?.sample_values !== null &&
    targetColumn?.sample_values !== undefined &&
    targetColumn.sample_values.length === 2;

  if (hasRealLabels && targetColumn?.sample_values) {
    const [majorityLabel, minorityLabel] = targetColumn.sample_values;
    return (
      <div className="space-y-2.5">
        <Bar label={majorityLabel} share={majorityShare} emphasis={false} />
        <Bar label={minorityLabel} share={minorityShare} emphasis={true} />
      </div>
    );
  }

  // Multiclass, or a binary target whose level names were not carried in
  // the profile - the ratio is still real, the class names are not, so only
  // the ratio is shown.
  return (
    <p className="text-secondary-size text-text-secondary">
      Majority to minority class ratio:{" "}
      <span className="font-mono text-text-primary">{classBalanceRatio.toFixed(2)}:1</span>
    </p>
  );
}
