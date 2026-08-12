/**
 * One numbered preprocessing step, with the connector rail from the step 4
 * mock so the sequence reads as a pipeline rather than a bulleted list.
 *
 * The targeted columns get their own sunken mono block, again from the mock
 * ("Targeted: ['age', 'income_est', 'credit_score']"), because they are
 * literal column names out of the dataset - the clearest case in this app
 * for the sans/mono split the design system is built on.
 */

import type { PreprocessingStep as PreprocessingStepType } from "../../types";

export function PreprocessingStep({
  step,
  index,
  isLast,
}: {
  step: PreprocessingStepType;
  index: number;
  isLast: boolean;
}) {
  return (
    <li className="flex gap-4">
      <div className="flex shrink-0 flex-col items-center">
        <span className="flex size-7 items-center justify-center rounded-full bg-accent-subtle font-mono text-data-sm font-bold text-accent-ink">
          {index + 1}
        </span>
        {!isLast ? <span className="mt-1 w-px flex-1 bg-border" aria-hidden /> : null}
      </div>

      <div className={`min-w-0 flex-1 ${isLast ? "" : "pb-6"}`}>
        <p className="text-body font-semibold text-text-primary">{step.step}</p>
        <p className="mt-1 max-w-[var(--prose-max-width)] text-secondary-size leading-relaxed text-text-secondary">
          {step.rationale}
        </p>
        {step.columns.length > 0 ? (
          <p className="mt-3 overflow-x-auto rounded-sm bg-sunken px-3 py-2 font-mono text-data-sm text-text-secondary">
            <span className="text-text-tertiary">Targeted: </span>
            {step.columns.join(", ")}
          </p>
        ) : null}
      </div>
    </li>
  );
}
