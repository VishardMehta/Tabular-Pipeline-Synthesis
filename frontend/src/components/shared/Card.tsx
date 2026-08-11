/**
 * A card groups information that belongs together - section 14. It is not
 * the default wrapper for every piece of content; whitespace and grouping
 * come first (Rule 2). Screens that need only a heading and a stat row use
 * plain layout, not a card around each stat.
 */

import type { HTMLAttributes, ReactNode } from "react";

export function Card({
  children,
  className = "",
  ...rest
}: { children: ReactNode } & HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-lg border border-border bg-surface p-6 shadow-xs ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export function SectionHeading({
  children,
  action,
}: {
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-center justify-between gap-4">
      <h2 className="text-heading font-heading text-text-primary">{children}</h2>
      {action}
    </div>
  );
}
