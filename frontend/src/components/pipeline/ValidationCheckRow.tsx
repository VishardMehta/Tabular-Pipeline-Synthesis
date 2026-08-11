/**
 * One row of a real ValidationReport.checks entry - never a hand-picked
 * subset. check_id, title, severity, message and details all come straight
 * from validation.py; nothing here is invented (no "Security scan (Bandit)"
 * or "Type checking (MyPy)" - those checks do not exist in this system).
 */

import { CheckCircleIcon, InfoCircleIcon, WarningTriangleIcon, XCircleIcon } from "../shared/icons";
import type { ValidationCheck } from "../../types";

function rowTone(check: ValidationCheck) {
  if (check.passed) return { icon: CheckCircleIcon, color: "text-success" };
  if (check.severity === "error") return { icon: XCircleIcon, color: "text-error" };
  if (check.severity === "warning") return { icon: WarningTriangleIcon, color: "text-warning" };
  return { icon: InfoCircleIcon, color: "text-text-tertiary" };
}

export function ValidationCheckRow({ check, index }: { check: ValidationCheck; index: number }) {
  const { icon: Icon, color } = rowTone(check);
  return (
    <li
      className="stagger-row flex gap-3 border-b border-separator py-3 last:border-0"
      style={{ "--stagger-index": index } as React.CSSProperties}
    >
      <Icon className={`mt-0.5 size-4.5 shrink-0 ${color}`} />
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-2 text-secondary-size font-medium text-text-primary">
          {check.title}
          <span className="text-caption font-normal uppercase tracking-wide text-text-tertiary">
            {check.severity}
          </span>
        </p>
        <p className="mt-0.5 text-secondary-size leading-relaxed text-text-secondary">
          {check.message}
        </p>
        {check.details.length > 0 ? (
          <p className="mt-1 font-mono text-caption text-text-tertiary">{check.details.join(", ")}</p>
        ) : null}
      </div>
    </li>
  );
}
