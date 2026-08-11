/** Screen 3: the plan the model committed to before it wrote any code. */

import { Button, Card, NotExecutedNotice, SectionTitle } from "../components/ui";
import type { GenResult } from "../types";

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
    <div className="space-y-4">
      <Card>
        <SectionTitle>Analysis</SectionTitle>
        <p className="text-sm leading-relaxed text-slate-700">{result.analysis_summary}</p>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
          <span>
            Task <strong>{result.problem_type.replace(/_/g, " ")}</strong>
          </span>
          <span>
            Target <strong>{result.target_column}</strong>
          </span>
          <span>
            Metric <strong>{result.primary_metric}</strong>
          </span>
        </div>
      </Card>

      <Card>
        <SectionTitle>Dropped columns ({result.dropped_columns.length})</SectionTitle>
        <ul className="space-y-2">
          {result.dropped_columns.map((dropped) => (
            <li key={dropped.column} className="text-sm">
              <span className="font-medium text-slate-900">{dropped.column}</span>
              <span className="text-slate-600"> - {dropped.reason}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionTitle>Preprocessing ({result.preprocessing.length} steps)</SectionTitle>
        <ol className="space-y-3">
          {result.preprocessing.map((step, index) => (
            <li key={step.step} className="text-sm">
              <p className="font-medium text-slate-900">
                {index + 1}. {step.step}
              </p>
              <p className="mt-0.5 text-xs text-slate-500">{step.columns.join(", ")}</p>
              <p className="mt-1 text-slate-600">{step.rationale}</p>
            </li>
          ))}
        </ol>
      </Card>

      <Card>
        <SectionTitle>Candidate models</SectionTitle>
        <ul className="space-y-3">
          {result.candidate_models.map((model) => (
            <li key={model.name} className="text-sm">
              <p className="font-medium text-slate-900">
                {model.name}
                <span className="ml-2 text-xs font-normal text-slate-500">{model.library}</span>
              </p>
              <p className="mt-1 text-slate-600">{model.rationale}</p>
            </li>
          ))}
        </ul>
        {/* No scores here, and there is no field that could carry one. */}
        <div className="mt-4">
          <NotExecutedNotice />
        </div>
      </Card>

      <Card>
        <SectionTitle>Validation strategy</SectionTitle>
        <p className="text-sm leading-relaxed text-slate-700">{result.validation_strategy}</p>
      </Card>

      <Card>
        <SectionTitle>Risks ({result.risks.length})</SectionTitle>
        <ul className="list-disc space-y-2 pl-5">
          {result.risks.map((risk) => (
            <li key={risk} className="text-sm text-slate-700">
              {risk}
            </li>
          ))}
        </ul>
      </Card>

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Back to profile
        </Button>
        <Button onClick={onViewCode}>View code</Button>
      </div>
    </div>
  );
}
