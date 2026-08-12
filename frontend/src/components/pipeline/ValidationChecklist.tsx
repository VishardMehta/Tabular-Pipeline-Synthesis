/**
 * The full static-check report. Every check in ValidationReport.checks is
 * rendered - passes included - because "12 checks ran and all passed" is a
 * different and much stronger statement than "no problems shown".
 *
 * Reduced motion comes from framer-motion's useReducedMotion rather than the
 * `typeof window !== "undefined" && window.matchMedia(...).matches` expression
 * the source component uses. That expression is read once during render and
 * never updates, so a reader who turns the preference on mid-session keeps the
 * animations until a remount. The hook subscribes to the media query.
 */

import { useReducedMotion } from "framer-motion";
import { StatusBadge } from "../shared/StatusBadge";
import { ValidationCheckRow } from "./ValidationCheckRow";
import type { ValidationReport } from "../../types";

function summary(report: ValidationReport): string {
  if (report.passed) return "All checks passed";
  const parts: string[] = [];
  if (report.error_count > 0) {
    parts.push(`${report.error_count} error${report.error_count === 1 ? "" : "s"}`);
  }
  if (report.warning_count > 0) {
    parts.push(`${report.warning_count} warning${report.warning_count === 1 ? "" : "s"}`);
  }
  return parts.join(", ");
}

export function ValidationChecklist({ report }: { report: ValidationReport }) {
  const reducedMotion = useReducedMotion() ?? false;
  const passedCount = report.checks.filter((check) => check.passed).length;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div>
          <h2 className="text-heading font-heading text-text-primary">Static checks</h2>
          <p className="mt-0.5 font-mono text-data-sm text-text-tertiary">
            {passedCount}/{report.checks.length} passed
          </p>
        </div>
        <StatusBadge tone={report.passed ? "success" : report.error_count > 0 ? "error" : "warning"}>
          {summary(report)}
        </StatusBadge>
      </div>

      <ul>
        {report.checks.map((check, index) => (
          <ValidationCheckRow
            key={check.check_id}
            check={check}
            index={index}
            reducedMotion={reducedMotion}
          />
        ))}
      </ul>
    </div>
  );
}
