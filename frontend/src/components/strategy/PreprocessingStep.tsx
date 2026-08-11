import type { PreprocessingStep as PreprocessingStepType } from "../../types";

export function PreprocessingStep({
  step,
  index,
}: {
  step: PreprocessingStepType;
  index: number;
}) {
  return (
    <div className="flex gap-4">
      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-secondary text-caption font-medium text-text-secondary">
        {index + 1}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-secondary-size font-medium text-text-primary">{step.step}</p>
        <p className="mt-0.5 font-mono text-caption text-text-tertiary">{step.columns.join(", ")}</p>
        <p className="mt-1.5 text-secondary-size leading-relaxed text-text-secondary">
          {step.rationale}
        </p>
      </div>
    </div>
  );
}
