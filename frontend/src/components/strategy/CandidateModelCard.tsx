/**
 * Section 14 explicitly lists "candidate model" as a legitimate card use,
 * unlike the surrounding Sections. Carries no score of any kind - GenResult
 * has no field that could hold one, and Rule 6 says never call an
 * unexecuted model the "best model".
 *
 * The first card is labelled "Implemented in code", not "best" or
 * "strongest" - that is a structural fact anyone can check by reading
 * pipeline.py (GenResult.candidate_models's own description: "The first one
 * is what the code implements"), not a performance claim about a model that
 * has never been run.
 */

import type { CandidateModel } from "../../types";

export function CandidateModelCard({
  model,
  rank,
}: {
  model: CandidateModel;
  rank: number;
}) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-secondary-size font-semibold text-text-primary">{model.name}</p>
        {rank === 0 ? (
          <span className="rounded-full bg-accent-subtle px-2 py-0.5 text-caption font-caption text-accent">
            Implemented in code
          </span>
        ) : null}
      </div>
      <p className="mt-0.5 text-caption text-text-tertiary">{model.library}</p>
      <p className="mt-2 text-secondary-size leading-relaxed text-text-secondary">
        {model.rationale}
      </p>
    </div>
  );
}
