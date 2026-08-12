/** Screen 4: the plan the model committed to before it wrote any code. */

import { Button } from "../components/shared/Button";
import { Card, CardHeader } from "../components/shared/Card";
import {
  ArrowRightIcon,
  ChevronLeftIcon,
  ListOrderedIcon,
  ShieldCheckIcon,
  WarningTriangleIcon,
} from "../components/shared/icons";
import { CandidateModelCard } from "../components/strategy/CandidateModelCard";
import { DroppedColumnsTable } from "../components/strategy/DroppedColumnsTable";
import { PreprocessingStep } from "../components/strategy/PreprocessingStep";
import { StageIntro } from "../components/layout/StageIntro";
import type { GenResult, Metric, ProblemType } from "../types";

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

const PROBLEM_LABEL: Record<ProblemType, string> = {
  binary_classification: "Binary classification",
  multiclass_classification: "Multiclass classification",
  regression: "Regression",
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
    <div className="space-y-6">
      <StageIntro
        stage={4}
        trail={<span className="font-mono normal-case tracking-normal text-text-secondary">{result.target_column}</span>}
        title="A strategy before code."
        description={<p>
            The plan committed to before any code was written. Review the preprocessing and the
            candidate architectures before reading the pipeline.
        </p>}
        action={<Button onClick={onViewCode} iconRight={<ArrowRightIcon className="size-4" />}>View pipeline</Button>}
      />

      {/* The three decisions that determine everything below, as facts. */}
      <dl className="grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-3">
        {[
          { label: "Problem type", value: PROBLEM_LABEL[result.problem_type] },
          { label: "Target column", value: result.target_column },
          { label: "Primary metric", value: METRIC_LABEL[result.primary_metric] },
        ].map((fact) => (
          <div key={fact.label} className="bg-surface px-5 py-4">
            <dt className="label-caps text-text-tertiary">{fact.label}</dt>
            <dd className="mt-1.5 truncate font-mono text-data text-text-primary">{fact.value}</dd>
          </div>
        ))}
      </dl>

      <Card>
        <CardHeader eyebrow="Why this plan" title="Analysis summary" />
        <p className="max-w-[var(--prose-max-width)] text-body leading-relaxed text-text-secondary">
          {result.analysis_summary}
        </p>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] lg:items-start">
        <div className="space-y-6">
          <Card>
            <CardHeader
              icon={<ListOrderedIcon className="size-5 text-accent" />}
              title="Preprocessing pipeline"
              action={
                <span className="label-caps text-text-tertiary">
                  {result.preprocessing.length} {result.preprocessing.length === 1 ? "step" : "steps"}
                </span>
              }
            />
            {result.preprocessing.length > 0 ? (
              <ol>
                {result.preprocessing.map((step, index) => (
                  <PreprocessingStep
                    key={step.step + index}
                    step={step}
                    index={index}
                    isLast={index === result.preprocessing.length - 1}
                  />
                ))}
              </ol>
            ) : (
              <p className="rounded-sm bg-sunken px-4 py-3 font-mono text-data-sm text-text-secondary">
                No preprocessing steps were declared for this dataset.
              </p>
            )}
          </Card>

          <Card>
            <CardHeader
              title="Dropped columns"
              action={
                <span className="label-caps text-text-tertiary">
                  {result.dropped_columns.length} dropped
                </span>
              }
            />
            <DroppedColumnsTable columns={result.dropped_columns} />
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader
              icon={<ShieldCheckIcon className="size-5 text-accent" />}
              title="Validation strategy"
            />
            <div className="mb-4 rounded-sm border border-border bg-sunken px-4 py-3">
              <p className="label-caps text-text-tertiary">Primary metric</p>
              <p className="mt-1 font-mono text-data font-semibold text-text-primary">
                {METRIC_LABEL[result.primary_metric]}
              </p>
            </div>
            <p className="border-l-2 border-accent pl-4 text-secondary-size leading-relaxed text-text-secondary">
              {result.validation_strategy}
            </p>
          </Card>

          <section>
            <div className="mb-3 flex items-baseline justify-between gap-3">
              <h2 className="text-heading font-heading text-text-primary">
                Candidate architectures
              </h2>
              <span className="label-caps text-text-tertiary">
                {result.candidate_models.length}{" "}
                {result.candidate_models.length === 1 ? "model" : "models"}
              </span>
            </div>
            <div className="space-y-3">
              {result.candidate_models.map((model, index) => (
                <CandidateModelCard key={model.name} model={model} rank={index} />
              ))}
            </div>
            <p className="mt-3 font-mono text-data-sm leading-relaxed text-text-tertiary">
              None of these has been run. There are no measured scores anywhere in this result.
            </p>
          </section>

          {result.risks.length > 0 ? (
            <Card>
              <CardHeader
                icon={<WarningTriangleIcon className="size-5 text-warning" />}
                title="Risks"
                action={<span className="label-caps text-text-tertiary">{result.risks.length}</span>}
              />
              <ul className="space-y-3">
                {result.risks.map((risk) => (
                  <li
                    key={risk}
                    className="border-l-2 border-warning-bar pl-4 text-secondary-size leading-relaxed text-text-secondary"
                  >
                    {risk}
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="secondary" onClick={onBack} icon={<ChevronLeftIcon className="size-4" />}>
          Back to profile
        </Button>
        <Button onClick={onViewCode} iconRight={<ArrowRightIcon className="size-4" />}>
          View pipeline
        </Button>
      </div>
    </div>
  );
}
