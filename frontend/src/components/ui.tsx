/**
 * Shared presentational pieces. Stage 0 styling: legible, not designed.
 * Stage 5 replaces all of this against the frozen visual spec.
 */

import type { ReactNode } from "react";
import type { ColumnFlag, ErrorDetail } from "../types";

export function Card({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">{children}</div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">{children}</h2>;
}

export function Button({
  children,
  onClick,
  disabled,
  variant = "primary",
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary";
}) {
  const base =
    "rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40";
  const styles =
    variant === "primary"
      ? "bg-slate-900 text-white hover:bg-slate-700"
      : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50";
  return (
    <button className={`${base} ${styles}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

/** Flags are advisory findings, so they are coloured by concern, not by pass or fail. */
const FLAG_STYLES: Record<ColumnFlag, string> = {
  potential_leakage: "bg-red-100 text-red-800",
  all_missing: "bg-red-100 text-red-800",
  high_missing: "bg-amber-100 text-amber-800",
  quasi_constant: "bg-amber-100 text-amber-800",
  constant: "bg-amber-100 text-amber-800",
  numeric_as_string: "bg-amber-100 text-amber-800",
  id_like: "bg-slate-200 text-slate-700",
  high_cardinality: "bg-slate-200 text-slate-700",
};

export function FlagBadge({ flag }: { flag: ColumnFlag }) {
  return (
    <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${FLAG_STYLES[flag]}`}>
      {flag.replace(/_/g, " ")}
    </span>
  );
}

export function ErrorBanner({
  detail,
  onRetry,
  onDismiss,
}: {
  detail: ErrorDetail;
  onRetry?: () => void;
  onDismiss: () => void;
}) {
  return (
    <div className="mb-4 flex items-start gap-4 rounded-md border border-red-200 bg-red-50 p-4">
      <div className="flex-1">
        <p className="text-sm font-semibold text-red-900">{detail.code}</p>
        <p className="mt-1 text-sm text-red-800">{detail.message}</p>
      </div>
      {detail.retryable && onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
      <Button variant="secondary" onClick={onDismiss}>
        Dismiss
      </Button>
    </div>
  );
}

/** Renders on every screen that shows generated code. Non-negotiable in MVP-1. */
export function NotExecutedNotice() {
  return (
    <div className="rounded-md border border-slate-300 bg-slate-100 px-3 py-2 text-xs text-slate-600">
      This pipeline has not been executed. No metric shown anywhere in this tool is a
      measured result.
    </div>
  );
}

export function Bar({ value, tone = "slate" }: { value: number; tone?: "slate" | "amber" }) {
  const colour = tone === "amber" ? "bg-amber-500" : "bg-slate-400";
  return (
    <div className="h-1.5 w-16 overflow-hidden rounded bg-slate-200">
      <div className={`h-full ${colour}`} style={{ width: `${Math.min(value, 1) * 100}%` }} />
    </div>
  );
}
