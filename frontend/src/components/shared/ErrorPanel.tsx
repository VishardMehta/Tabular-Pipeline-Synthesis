/**
 * Renders one ErrorDetail from the API error envelope. Section 23: specific,
 * actionable, calm, human-readable - never a raw stack trace. The code is
 * shown as a small technical label for anyone who needs to reference it
 * (support, a bug report), the message is the thing a person actually reads.
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
      className="mb-6 flex items-start gap-3 rounded-md border border-error-subtle bg-error-subtle px-4 py-3.5"
    >
      <WarningTriangleIcon className="mt-0.5 size-4.5 shrink-0 text-error" />
      <div className="min-w-0 flex-1">
        <p className="text-secondary-size font-mono text-caption uppercase tracking-wide text-error/80">
          {detail.code}
        </p>
        <p className="mt-0.5 text-secondary-size leading-relaxed text-text-primary">
          {detail.message}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {detail.retryable && onRetry ? <RetryButton onClick={onRetry} /> : null}
        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="rounded-sm px-2 py-1.5 text-secondary-size text-text-secondary hover:bg-white/50"
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}
