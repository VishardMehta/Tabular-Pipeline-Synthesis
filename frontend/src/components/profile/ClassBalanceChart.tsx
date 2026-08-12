/**
 * Class balance as the single stacked bar from the step 3 mock: one track,
 * the minority share in primary blue, the majority in a neutral, with the
 * two labels reading out beneath it left and right.
 *
 * Real per-class labels only exist for binary classification: the target's
 * own ColumnProfile.sample_values, when populated, lists level names ordered
 * by descending frequency (profiler.py builds it from value_counts().head()),
 * so sample_values[0] is genuinely the majority label and sample_values[1]
 * the minority - not a guess. class_balance_ratio (n_majority / n_minority)
 * then gives the exact split via ratio / (1 + ratio) and 1 / (1 + ratio).
 * For multiclass, one ratio cannot be attributed to specific class names
 * without inventing which classes those are, so this falls back to an
 * unlabelled ratio rather than naming classes the profile never named.
 *
 * The "Balanced / Imbalanced" wording is a description of the ratio that is
 * already on screen next to it, not a hidden threshold judgement - the
 * reader can check it against the number themselves.
 */

import type { ColumnProfile, ProblemType } from "../../types";

const IMBALANCE_DESCRIPTION_RATIO = 1.5;

function formatShare(share: number): string {
  const pct = share * 100;
  return `${pct.toFixed(pct < 10 ? 1 : 0)}%`;
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
  const imbalanced = classBalanceRatio >= IMBALANCE_DESCRIPTION_RATIO;

  const labels =
    problemType === "binary_classification" && targetColumn?.sample_values?.length === 2
      ? targetColumn.sample_values
      : null;

  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <p className="label-caps text-text-tertiary">Class balance</p>
        <p
          className={`font-mono text-data-sm font-semibold ${
            imbalanced ? "text-error" : "text-success"
          }`}
        >
          {imbalanced ? "Imbalanced" : "Balanced"} ({classBalanceRatio.toFixed(2)}:1)
        </p>
      </div>

      <div
        className="flex h-2.5 w-full overflow-hidden rounded-full bg-border-strong"
        role="img"
        aria-label={
          labels
            ? `${labels[0]} ${formatShare(majorityShare)}, ${labels[1]} ${formatShare(minorityShare)}`
            : `Majority to minority class ratio ${classBalanceRatio.toFixed(2)} to 1`
        }
      >
        <div className="h-full bg-accent" style={{ width: `${minorityShare * 100}%` }} />
      </div>

      {labels ? (
        <div className="mt-2 flex items-baseline justify-between gap-3 font-mono text-data-sm">
          <span className="min-w-0 truncate text-accent-ink">
            {labels[1]}: {formatShare(minorityShare)}
          </span>
          <span className="min-w-0 truncate text-text-secondary">
            {labels[0]}: {formatShare(majorityShare)}
          </span>
        </div>
      ) : (
        // Multiclass, or a binary target whose level names were not carried
        // in the profile. The ratio is real; the class names are not.
        <p className="mt-2 font-mono text-data-sm text-text-tertiary">
          Class names are not carried in the profile for this target, so only the ratio is shown.
        </p>
      )}
    </div>
  );
}
