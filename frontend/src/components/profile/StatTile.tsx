/**
 * One headline number from the profile.
 *
 * The layout is straight from the step 3 mock: uppercase mono label, then a
 * large mono figure, in a bordered white tile. A tile that needs attention
 * grows a 2px coloured left bar and a status icon - the bar alone would be
 * colour as the only signal, which is not allowed, so the two always travel
 * together.
 *
 * `note` is for the qualifier the mock sets beside the number in a smaller
 * face ("4,210 (0.35%)", "12% avg/col") - it belongs to the value, not to
 * the label, so it sits on the same baseline.
 */

import { WarningTriangleIcon, XCircleIcon } from "../shared/icons";

type Tone = "neutral" | "warning" | "error";

const TONE_BAR: Record<Tone, string> = {
  neutral: "border-l-transparent",
  warning: "border-l-warning-bar",
  error: "border-l-error",
};

const TONE_ICON: Record<Tone, typeof WarningTriangleIcon | null> = {
  neutral: null,
  warning: WarningTriangleIcon,
  error: XCircleIcon,
};

const TONE_ICON_COLOR: Record<Tone, string> = {
  neutral: "",
  warning: "text-warning",
  error: "text-error",
};

export function StatTile({
  label,
  value,
  note,
  tone = "neutral",
  toneLabel,
}: {
  label: string;
  value: string;
  note?: string;
  tone?: Tone;
  /** Read out with the icon so the tone is never conveyed by colour alone. */
  toneLabel?: string;
}) {
  const Icon = TONE_ICON[tone];
  return (
    <div
      className={`rounded-lg border border-l-2 border-border bg-surface px-5 py-4 ${TONE_BAR[tone]}`}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <p className="label-caps text-text-tertiary">{label}</p>
        {Icon ? (
          <span className={`shrink-0 ${TONE_ICON_COLOR[tone]}`} title={toneLabel}>
            <Icon className="size-4" />
            <span className="sr-only">{toneLabel ?? tone}</span>
          </span>
        ) : null}
      </div>
      <p className="flex items-baseline gap-2">
        <span className="font-mono text-[1.75rem] font-semibold leading-8 tracking-tight text-text-primary">
          {value}
        </span>
        {note ? <span className="font-mono text-data-sm text-text-tertiary">{note}</span> : null}
      </p>
    </div>
  );
}
