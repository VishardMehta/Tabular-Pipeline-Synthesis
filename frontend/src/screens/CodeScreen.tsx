/** Screen 5: the generated code and the validation checklist. */

import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ChevronLeftIcon } from "../components/shared/icons";
import { CodeBlock } from "../components/pipeline/CodeBlock";
import { UnexecutedNotice } from "../components/pipeline/UnexecutedNotice";
import { ValidationChecklist } from "../components/pipeline/ValidationChecklist";
import { StageIntro } from "../components/layout/StageIntro";
import type { GenResult, UsageResponse, ValidationReport } from "../types";

const number = new Intl.NumberFormat("en-US");

function measuredLatency(usage: UsageResponse) {
  const total = usage.attempts.reduce((sum, attempt) => sum + attempt.latency_ms, 0);
  return total < 1_000 ? `${total} ms` : `${(total / 1_000).toFixed(1)} s`;
}

export function CodeScreen({
  result,
  validation,
  usage,
  onBack,
  onRestart,
}: {
  result: GenResult;
  validation: ValidationReport;
  usage: UsageResponse | null;
  onBack: () => void;
  onRestart: () => void;
}) {
  return (
    <div className="space-y-6">
      <StageIntro
        stage={5}
        trail={<span className="font-mono normal-case tracking-normal text-text-secondary">{result.target_column}</span>}
        title="Your pipeline, ready to inspect."
        description={<p className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span>Written for target</span>
          <span className="rounded-tag bg-accent-subtle px-2 py-0.5 font-mono text-data text-accent-ink">
            {result.target_column}
          </span>
          <span>- read it before you run it.</span>
        </p>}
      />

      <UnexecutedNotice />

      {usage ? (
        <Card>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="label-caps text-text-tertiary">Generation record</p>
              <p className="mt-1 text-body-sm text-text-secondary">
                Measured provider usage, not a pipeline-performance score.
              </p>
            </div>
            {usage.attempts.at(-1) ? (
              <span className="rounded-tag bg-sunken px-2 py-1 font-mono text-data-sm text-text-secondary">
                {usage.attempts.at(-1)?.provider} / {usage.attempts.at(-1)?.model}
              </span>
            ) : null}
          </div>
          <dl className="mt-5 grid gap-4 border-t border-separator pt-4 sm:grid-cols-3">
            <div>
              <dt className="label-caps text-text-tertiary">Provider attempts</dt>
              <dd className="mt-1 font-mono text-body text-text-primary">{usage.total_attempts}</dd>
            </div>
            <div>
              <dt className="label-caps text-text-tertiary">Tokens</dt>
              <dd className="mt-1 font-mono text-body text-text-primary">
                {number.format(usage.total_input_tokens + usage.total_output_tokens)}
              </dd>
            </div>
            <div>
              <dt className="label-caps text-text-tertiary">Provider time</dt>
              <dd className="mt-1 font-mono text-body text-text-primary">{measuredLatency(usage)}</dd>
            </div>
          </dl>
        </Card>
      ) : null}

      {/* The validation report comes before the code, not after: a person
          deciding whether to trust this pipeline should see what was checked
          first, not discover it below a 200-line scroll. */}
      <Card padded={false} className="overflow-hidden">
        <ValidationChecklist report={validation} />
      </Card>

      <CodeBlock code={result.code} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="secondary" onClick={onBack} icon={<ChevronLeftIcon className="size-4" />}>
          Back to strategy
        </Button>
        <Button variant="secondary" onClick={onRestart}>
          Start over
        </Button>
      </div>
    </div>
  );
}
