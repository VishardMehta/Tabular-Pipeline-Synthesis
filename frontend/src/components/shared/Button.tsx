/**
 * Three emphasis levels. A screen should make its next action obvious, which
 * means at most one primary button per screen - that discipline is enforced
 * by callers, not here.
 *
 * DESIGN.md: 4px radius, solid #0066FF primary, ghost secondary with a
 * hairline border, no shadow. Deliberately no press-scale: "on hover, cards
 * do not lift... this maintains the Precision feel - stability over motion".
 * The feedback is a colour transition, which is also what survives
 * prefers-reduced-motion intact.
 */

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { SpinnerIcon } from "./icons";

type Variant = "primary" | "secondary" | "tertiary";

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  children: ReactNode;
  variant?: Variant;
  loading?: boolean;
  icon?: ReactNode;
  iconRight?: ReactNode;
}

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    "bg-accent text-text-on-accent hover:bg-accent-hover disabled:bg-border-strong disabled:text-white",
  secondary:
    "border border-border bg-surface text-text-primary hover:border-border-strong hover:bg-surface-secondary disabled:text-text-disabled disabled:hover:border-border disabled:hover:bg-surface",
  tertiary:
    "text-accent-ink hover:bg-accent-subtle disabled:text-text-disabled disabled:hover:bg-transparent",
};

export function Button({
  children,
  variant = "primary",
  loading = false,
  icon,
  iconRight,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-sm px-4 py-2 text-secondary-size font-semibold transition-colors duration-150 ease-out disabled:cursor-not-allowed ${VARIANT_STYLES[variant]}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...rest}
    >
      {loading ? <SpinnerIcon className="size-4 animate-spin" /> : icon}
      {children}
      {loading ? null : iconRight}
    </button>
  );
}
