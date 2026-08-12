/**
 * Surface 1: white on the grey canvas, 8px radius, one hairline border, no
 * shadow. DESIGN.md is explicit that depth here is architectural - the
 * arrangement of bordered panels - not elevation.
 *
 * `padded={false}` is for cards whose content runs edge to edge, which is
 * every table in this app: a table's own row padding should reach the card
 * border, not sit inside a second inset.
 */

import type { HTMLAttributes, ReactNode } from "react";

export function Card({
  children,
  className = "",
  padded = true,
  ...rest
}: { children: ReactNode; padded?: boolean } & HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-lg border border-border bg-surface ${padded ? "p-6" : ""} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

/**
 * The uppercase mono eyebrow above a card's title. This pairing - small caps
 * mono label, then a sans heading - is the system's main way of labelling a
 * region without spending a heading level on it.
 */
export function CardHeader({
  eyebrow,
  title,
  action,
  icon,
}: {
  eyebrow?: string;
  title: ReactNode;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4 border-b border-separator pb-4">
      <div className="min-w-0">
        {eyebrow ? <p className="label-caps mb-1.5 text-text-tertiary">{eyebrow}</p> : null}
        <h2 className="flex items-center gap-2 text-heading font-heading text-text-primary">
          {icon}
          {title}
        </h2>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

