/**
 * A candidate model. Carries no score of any kind - GenResult has no field
 * that could hold one, and an unexecuted model is never the "best model".
 *
 * The first card is labelled "Implemented in code", not "best", "strongest"
 * or the mock's "Fast" / "Robust" / "Baseline". Those three are unmeasured
 * performance claims about code that has never run. "Implemented in code" is
 * a structural fact anyone can verify by reading pipeline.py - it restates
 * GenResult.candidate_models's own contract, that the first entry is the one
 * the code implements.
 */

import type { CandidateModel } from "../../types";

export function CandidateModelCard({ model, rank }: { model: CandidateModel; rank: number }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 transition-colors duration-150 hover:border-border-strong">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-body font-semibold text-text-primary">{model.name}</p>
          <p className="mt-0.5 font-mono text-data-sm text-text-tertiary">{model.library}</p>
        </div>
        {rank === 0 ? (
          <span className="shrink-0 rounded-tag bg-accent-subtle px-2 py-1 font-mono text-data-sm font-medium text-accent-ink">
            In code
          </span>
        ) : null}
      </div>
      <p className="mt-3 text-secondary-size leading-relaxed text-text-secondary">
        {model.rationale}
      </p>
    </div>
  );
}
