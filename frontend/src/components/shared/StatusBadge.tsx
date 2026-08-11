/**
 * A semantic status label. Section 5.3: color is never the only signal, so
 * every tone pairs a fixed icon with the text - a color-blind reader or a
 * grayscale printout still gets the same information.
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
  success: <CheckCircleIcon className="size-3.5" />,
  warning: <WarningTriangleIcon className="size-3.5" />,
  error: <XCircleIcon className="size-3.5" />,
  info: <InfoCircleIcon className="size-3.5" />,
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
   * Override the default tone icon. Pass `null` explicitly to render no
   * icon at all (e.g. a dense table of pills where the text label alone
   * already carries the meaning); omit the prop to use the tone's default.
   */
  icon?: ReactNode | null;
}) {
  const resolvedIcon = icon === undefined ? TONE_ICON[tone] : icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-caption font-caption ${TONE_STYLES[tone]}`}
    >
      {resolvedIcon}
      {children}
    </span>
  );
}
