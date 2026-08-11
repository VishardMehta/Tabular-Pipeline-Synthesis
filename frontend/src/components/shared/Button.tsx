/**
 * Three emphasis levels, matching section 15 of the design doc. A screen
 * should make its next action obvious, which means at most one primary
 * button per screen - that discipline is enforced by callers, not here.
 */

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { SpinnerIcon } from "./icons";

type Variant = "primary" | "secondary" | "tertiary";

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  children: ReactNode;
  variant?: Variant;
  loading?: boolean;
  icon?: ReactNode;
}

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    "bg-accent text-text-on-accent shadow-xs hover:bg-accent-hover active:scale-[0.98] disabled:bg-text-disabled disabled:shadow-none",
  secondary:
    "border border-border bg-surface text-text-primary hover:bg-surface-hover active:scale-[0.98] disabled:text-text-disabled disabled:hover:bg-surface",
  tertiary:
    "text-accent hover:text-accent-hover underline-offset-4 hover:underline disabled:text-text-disabled disabled:hover:no-underline",
};

export function Button({
  children,
  variant = "primary",
  loading = false,
  icon,
  disabled,
  ...rest
}: ButtonProps) {
  const paddedVariant = variant === "tertiary" ? "px-1 py-1" : "px-4 py-2.5";
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-sm text-sm font-medium transition-[background-color,color,transform,opacity] duration-150 ease-out disabled:cursor-not-allowed disabled:active:scale-100 ${paddedVariant} ${VARIANT_STYLES[variant]}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...rest}
    >
      {loading ? <SpinnerIcon className="size-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}
