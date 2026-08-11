/**
 * Screen 4: the generated code and the validation checklist.
 *
 * Stage 0 renders the code in a plain <pre>. Syntax highlighting via shiki is a
 * stage 5 concern and would only obscure whether the contract works.
 */

import { Button, Card, NotExecutedNotice, SectionTitle } from "../components/ui";
import type { GenResult, ValidationCheck, ValidationReport } from "../types";

function CheckRow({ check }: { check: ValidationCheck }) {
  const tone = check.passed
    ? "text-emerald-700"
    : check.severity === "error"
      ? "text-red-700"
      : check.severity === "warning"
        ? "text-amber-700"
        : "text-slate-600";
  return (
    <li className="flex gap-3 py-2">
      <span className={`mt-0.5 font-mono text-sm ${tone}`}>{check.passed ? "PASS" : "FAIL"}</span>
      <div className="flex-1">
        <p className="text-sm font-medium text-slate-900">
          {check.title}
          <span className="ml-2 text-xs font-normal uppercase tracking-wide text-slate-400">
            {check.severity}
          </span>
        </p>
        <p className="mt-0.5 text-sm text-slate-600">{check.message}</p>
        {check.details.length > 0 ? (
          <p className="mt-1 font-mono text-xs text-slate-500">{check.details.join(", ")}</p>
        ) : null}
      </div>
    </li>
  );
}

export function CodeScreen({
  result,
  validation,
  onBack,
  onRestart,
}: {
  result: GenResult;
  validation: ValidationReport;
  onBack: () => void;
  onRestart: () => void;
}) {
  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <SectionTitle>Validation</SectionTitle>
          <span className="text-sm text-slate-600">
            {validation.error_count} errors, {validation.warning_count} warnings
          </span>
        </div>
        <ul className="divide-y divide-slate-100">
          {validation.checks.map((check) => (
            <CheckRow key={check.check_id} check={check} />
          ))}
        </ul>
      </Card>

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <SectionTitle>Pipeline</SectionTitle>
          <Button variant="secondary" onClick={() => navigator.clipboard.writeText(result.code)}>
            Copy
          </Button>
        </div>
        <NotExecutedNotice />
        <pre className="mt-3 max-h-[28rem] overflow-auto rounded-md bg-slate-900 p-4 text-xs leading-relaxed text-slate-100">
          <code>{result.code}</code>
        </pre>
      </Card>

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Back to strategy
        </Button>
        <Button variant="secondary" onClick={onRestart}>
          Start over
        </Button>
      </div>
    </div>
  );
}
