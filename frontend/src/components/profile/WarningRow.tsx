/**
 * One line in the Data quality summary - section 24's ranked list
 * (Missing values, Duplicate rows, Constant columns, ID-like columns,
 * Possible leakage). Icon-coded by tone, never color alone.
 */

import { CheckCircleIcon, InfoCircleIcon, WarningTriangleIcon, XCircleIcon } from "../shared/icons";
import type { BadgeTone } from "../shared/StatusBadge";

const ICON: Record<BadgeTone, typeof CheckCircleIcon> = {
  success: CheckCircleIcon,
  warning: WarningTriangleIcon,
  error: XCircleIcon,
  info: InfoCircleIcon,
  neutral: InfoCircleIcon,
};

const ICON_COLOR: Record<BadgeTone, string> = {
  success: "text-success",
  warning: "text-warning",
  error: "text-error",
  info: "text-info",
  neutral: "text-text-tertiary",
};

export function WarningRow({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: BadgeTone;
}) {
  const Icon = ICON[tone];
  return (
    <div className="flex items-center justify-between border-b border-separator py-2.5 last:border-0">
      <span className="flex items-center gap-2 text-secondary-size text-text-primary">
        <Icon className={`size-4 ${ICON_COLOR[tone]}`} />
        {label}
      </span>
      <span className="font-mono text-secondary-size text-text-secondary">{value}</span>
    </div>
  );
}
