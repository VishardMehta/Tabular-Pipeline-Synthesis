/**
 * Renders one ErrorDetail from the API error envelope: specific, actionable,
 * calm, human-readable - never a raw stack trace. The code is a small mono
 * label for anyone who needs to quote it (support, a bug report); the message
 * is the thing a person actually reads.
 *
 * The 2px left bar is the system's severity marker, reused from the stat
 * tiles - the same visual grammar for "this one needs attention" wherever it
 * appears.
 */

import { WarningTriangleIcon } from "./icons";
import { RetryButton } from "./RetryButton";
import type { ErrorDetail } from "../../types";

export function ErrorPanel({
  detail,
  onRetry,
  onDismiss,
}: {
  detail: ErrorDetail;
  onRetry?: () => void;
  onDismiss?: () => void;
}) {
  return (
    <div
      role="alert"
      className="mb-6 flex items-start gap-3 rounded-lg border border-error-border border-l-2 border-l-error bg-error-subtle px-4 py-3.5"
    >
      <WarningTriangleIcon className="mt-0.5 size-4 shrink-0 text-error" />
      <div className="min-w-0 flex-1">
        <p className="label-caps text-error">{detail.code}</p>
        <p className="mt-1 text-secondary-size text-text-primary">{detail.message}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {detail.retryable && onRetry ? <RetryButton onClick={onRetry} /> : null}
        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-sm px-2 py-2 text-secondary-size font-medium text-text-secondary transition-colors hover:bg-white/60 hover:text-text-primary"
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}
