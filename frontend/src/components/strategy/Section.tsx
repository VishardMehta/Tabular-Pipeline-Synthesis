/**
 * One block of the strategy document. Section 26: "This should feel like a
 * decision document... Avoid a chatbot-style interface." So the strategy
 * screen is one continuous document, not five separate cards - each Section
 * is a heading plus content, divided by a rule, not boxed on its own.
 */

import type { ReactNode } from "react";

export function Section({
  title,
  meta,
  children,
}: {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="border-b border-separator py-7 first:pt-0 last:border-0 last:pb-0">
      <div className="mb-4 flex items-baseline justify-between gap-4">
        <h3 className="text-heading font-heading text-text-primary">{title}</h3>
        {meta}
      </div>
      {children}
    </section>
  );
}
