/**
 * A small, self-contained line-icon set.
 *
 * No icon package is a project dependency, so these are hand-drawn to one
 * consistent stroke weight and viewbox rather than pulled from a library.
 * Semantic coverage follows section 31 of the design doc (checkmark.circle,
 * exclamationmark.triangle, xmark.circle, arrow.up, arrow.down, doc.on.doc)
 * without depending on SF Symbols, which is not usable on the web.
 */

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const base = {
  viewBox: "0 0 20 20",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M7 10.2l2 2 4-4.4" />
    </svg>
  );
}

export function WarningTriangleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3.5l7.5 13h-15z" strokeLinejoin="round" />
      <path d="M10 8.2v3.6" />
      <circle cx="10" cy="14.2" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function XCircleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M7.5 7.5l5 5M12.5 7.5l-5 5" />
    </svg>
  );
}

export function InfoCircleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M10 9.2v4.2" />
      <circle cx="10" cy="6.7" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function UploadArrowIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 13.5V4.5M6.2 8.2L10 4.5l3.8 3.7" />
      <path d="M4 15.5h12" />
    </svg>
  );
}

export function DownloadArrowIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 4.5v9M6.2 10.3L10 14l3.8-3.7" />
      <path d="M4 15.5h12" />
    </svg>
  );
}

export function CopyIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="7.25" y="7.25" width="8.5" height="8.5" rx="1.5" />
      <path d="M4.25 12.25v-7A1.5 1.5 0 015.75 3.5h7" />
    </svg>
  );
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7.5 4.5l6 5.5-6 5.5" />
    </svg>
  );
}

export function ChevronLeftIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12.5 4.5l-6 5.5 6 5.5" />
    </svg>
  );
}

export function SearchIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="8.75" cy="8.75" r="5" />
      <path d="M15.25 15.25l-3.4-3.4" />
    </svg>
  );
}

export function SpinnerIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden {...props}>
      <circle
        cx="10"
        cy="10"
        r="7.25"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeOpacity="0.2"
      />
      <path
        d="M17.25 10a7.25 7.25 0 00-7.25-7.25"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function DatasetIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="4.5" width="14" height="11" rx="1.5" />
      <path d="M3 8.5h14M8 8.5v7" />
    </svg>
  );
}

export function TargetIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="6.5" />
      <circle cx="10" cy="10" r="3" />
      <circle cx="10" cy="10" r="0.15" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function ChartIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 16V8.5M10 16V4M16 16v-5.5" />
      <path d="M3 16.5h14" />
    </svg>
  );
}

export function StrategyIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3.5v2M10 14.5v2M3.5 10h2M14.5 10h2" />
      <circle cx="10" cy="10" r="4" />
    </svg>
  );
}

export function PipelineIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7.5 5.5L4 10l3.5 4.5M12.5 5.5L16 10l-3.5 4.5" />
      <path d="M11 4.5l-2 11" />
    </svg>
  );
}
