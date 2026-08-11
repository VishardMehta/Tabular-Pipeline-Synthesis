/**
 * A loading placeholder shaped like the content it stands in for, never a
 * bare spinner. Used only where there is no more specific named-step
 * indicator to show - see Pipeline/UnexecutedNotice and the generation
 * step list for the named-progress case section 21 asks for instead.
 */

import type { CSSProperties } from "react";

export function Skeleton({
  className = "",
  style,
}: {
  className?: string;
  style?: CSSProperties;
}) {
  return <div className={`skeleton-shimmer rounded-sm ${className}`} style={style} aria-hidden />;
}

export function SkeletonText({ lines = 3, lastLineWidth = "60%" }: { lines?: number; lastLineWidth?: string }) {
  return (
    <div className="space-y-2" aria-hidden>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className="h-3.5"
          style={index === lines - 1 ? { width: lastLineWidth } : undefined}
        />
      ))}
    </div>
  );
}
