/**
 * A semantic status label. Colour is never the only signal, so every tone
 * pairs a fixed icon with the text - a colour-blind reader or a greyscale
 * printout still gets the same information.
 *
 * DESIGN.md: "Small, square-edged tags... light-tint background of the status
 * colour with high-contrast text." Square-edged, hence radius-tag rather than
 * a pill, and mono type because a status is technical content, not prose.
 */

import type { ReactNode } from "react";
import { CheckCircleIcon, InfoCircleIcon, WarningTriangleIcon, XCircleIcon } from "./icons";

export type BadgeTone = "success" | "warning" | "error" | "info" | "neutral";

const TONE_STYLES: Record<BadgeTone, string> = {
  success: "bg-success-subtle text-success",
  warning: "bg-warning-subtle text-warning",
  error: "bg-error-subtle text-error",
  info: "bg-info-subtle text-info",
  neutral: "bg-surface-secondary text-text-secondary",
};

const TONE_ICON: Record<BadgeTone, ReactNode> = {
  success: <CheckCircleIcon className="size-3.5 shrink-0" />,
  warning: <WarningTriangleIcon className="size-3.5 shrink-0" />,
  error: <XCircleIcon className="size-3.5 shrink-0" />,
  info: <InfoCircleIcon className="size-3.5 shrink-0" />,
  neutral: null,
};

export function StatusBadge({
  tone,
  children,
  icon,
}: {
  tone: BadgeTone;
  children: ReactNode;
  /**
   * Override the default tone icon. Pass `null` explicitly to render no icon
   * at all (a dense table of pills where the label alone already carries the
   * meaning); omit the prop to use the tone's default.
   */
  icon?: ReactNode | null;
}) {
  const resolvedIcon = icon === undefined ? TONE_ICON[tone] : icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-tag px-2 py-1 font-mono text-data-sm font-medium ${TONE_STYLES[tone]}`}
    >
      {resolvedIcon}
      {children}
    </span>
  );
}

/**
 * The dtype / inferred-type pill from the target table: light grey, no
 * border, mono, near-sharp corners. Distinct from StatusBadge because it
 * carries no status meaning at all and so must not borrow a status colour.
 */
export function DataTag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-block rounded-tag bg-surface-secondary px-1.5 py-0.5 font-mono text-data-sm text-text-secondary">
      {children}
    </span>
  );
}
