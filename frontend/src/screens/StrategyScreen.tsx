/** Screen 3: the plan the model committed to before it wrote any code. */

import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { CandidateModelCard } from "../components/strategy/CandidateModelCard";
import { DroppedColumnsTable } from "../components/strategy/DroppedColumnsTable";
import { PreprocessingStep } from "../components/strategy/PreprocessingStep";
import { Section } from "../components/strategy/Section";
import type { GenResult } from "../types";

const METRIC_LABEL: Record<string, string> = {
  accuracy: "Accuracy",
  f1: "F1 Score",
  f1_macro: "F1 Score (macro)",
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  rmse: "RMSE",
  mae: "MAE",
  r2: "R²",
};

export function StrategyScreen({
  result,
  onViewCode,
  onBack,
}: {
  result: GenResult;
  onViewCode: () => void;
  onBack: () => void;
}) {
  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-8">
        <h2 className="text-title font-title text-text-primary">Recommended strategy</h2>
        <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-secondary-size text-text-secondary">
          <span>{result.problem_type.replace(/_/g, " ")}</span>
          <span aria-hidden>&middot;</span>
          <span>
            Target <span className="font-mono text-text-primary">{result.target_column}</span>
          </span>
          <span aria-hidden>&middot;</span>
          <span>
            Metric{" "}
            <span className="font-medium text-text-primary">
              {METRIC_LABEL[result.primary_metric] ?? result.primary_metric}
            </span>
          </span>
        </p>
      </div>

      <Card>
        <Section title="Analysis">
          <p className="max-w-[var(--prose-max-width)] text-secondary-size leading-relaxed text-text-secondary">
            {result.analysis_summary}
          </p>
        </Section>

        <Section title="Dropped columns" meta={<Count value={result.dropped_columns.length} />}>
          <DroppedColumnsTable columns={result.dropped_columns} />
        </Section>

        <Section title="Preprocessing" meta={<Count value={result.preprocessing.length} />}>
          <div className="space-y-4">
            {result.preprocessing.map((step, index) => (
              <PreprocessingStep key={step.step + index} step={step} index={index} />
            ))}
          </div>
        </Section>

        <Section title="Candidate models" meta={<Count value={result.candidate_models.length} />}>
          <div className="space-y-3">
            {result.candidate_models.map((model, index) => (
              <CandidateModelCard key={model.name} model={model} rank={index} />
            ))}
          </div>
          <p className="mt-3 text-caption text-text-tertiary">
            Not executed - no candidate model here has a measured score.
          </p>
        </Section>

        <Section title="Validation">
          <p className="max-w-[var(--prose-max-width)] text-secondary-size leading-relaxed text-text-secondary">
            {result.validation_strategy}
          </p>
        </Section>

        <Section title="Risks" meta={<Count value={result.risks.length} />}>
          <ul className="space-y-2.5">
            {result.risks.map((risk) => (
              <li key={risk} className="flex gap-2.5 text-secondary-size leading-relaxed text-text-secondary">
                <span className="mt-0.5 text-warning" aria-hidden>
                  &#9650;
                </span>
                {risk}
              </li>
            ))}
          </ul>
        </Section>
      </Card>

      <div className="mt-6 flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Back to profile
        </Button>
        <Button onClick={onViewCode}>View pipeline</Button>
      </div>
    </div>
  );
}

function Count({ value }: { value: number }) {
  return <span className="text-caption text-text-tertiary">{value}</span>;
}
