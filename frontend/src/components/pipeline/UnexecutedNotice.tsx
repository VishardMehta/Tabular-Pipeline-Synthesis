/**
 * The persistent notice. Wording is exact and non-negotiable - do not touch
 * it, per the design brief. Full width, high visual weight, always visible
 * above the code (never behind a scroll, never as a dismissible toast).
 */

import { InfoCircleIcon } from "../shared/icons";

export function UnexecutedNotice() {
  return (
    <div className="flex w-full items-center gap-3 rounded-md border border-warning-subtle bg-warning-subtle px-4 py-3">
      <InfoCircleIcon className="size-4.5 shrink-0 text-warning" />
      <p className="text-secondary-size font-medium text-text-primary">
        This pipeline has not been executed. Static checks only.
      </p>
    </div>
  );
}
