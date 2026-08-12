/**
 * The persistent notice. Wording is exact and non-negotiable - do not touch
 * it. Full width, high visual weight, always visible above the code (never
 * behind a scroll, never as a dismissible toast).
 *
 * The mock pairs this banner with an "Execute Pipeline" button. There is no
 * execution endpoint in this system, so that button would either do nothing
 * or imply a capability that does not exist - it is cut, and the supporting
 * line says what the reader can actually do instead.
 */

import { WarningTriangleIcon } from "../shared/icons";

export function UnexecutedNotice() {
  return (
    <div
      role="status"
      className="flex w-full items-start gap-3 rounded-lg border border-warning-border border-l-2 border-l-warning-bar bg-warning-subtle px-5 py-4"
    >
      <WarningTriangleIcon className="mt-0.5 size-5 shrink-0 text-warning" />
      <div>
        <p className="text-body font-semibold text-text-primary">
          This pipeline has not been executed. Static checks only.
        </p>
        <p className="mt-1 text-secondary-size text-text-secondary">
          Nothing below was measured by running the code. Read it, then run it yourself in an
          environment you control.
        </p>
      </div>
    </div>
  );
}
