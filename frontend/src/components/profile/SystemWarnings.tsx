/**
 * Named, per-column findings - the "SYSTEM WARNINGS" panel from the original
 * step 3 export ("`churn_reason` has 0.99 association with the target and may
 * leak the outcome").
 *
 * This is the piece the counts alone cannot give you. "1 possible leakage" is
 * a number; "`leaky` has 0.99 purity association with the target" is something
 * a person can act on, and every part of it is already in the ProfileCard -
 * ColumnProfile.target_association, .association_method, .missing_pct and
 * .flags. Nothing here is inferred beyond formatting those fields.
 *
 * Two rules shape the wording:
 *   - target_association is never called a correlation. The method is named
 *     per column, because it genuinely differs (spearman, eta, purity).
 *   - a flag is a fact with a threshold behind it, not a decision, so every
 *     line says what was measured and leaves the judgement to the reader.
 */

import { InfoCircleIcon, WarningTriangleIcon, XCircleIcon } from "../shared/icons";
import type { ColumnProfile, ProfileCard } from "../../types";

type Severity = "error" | "warning" | "info";

interface Finding {
  column: string;
  severity: Severity;
  text: string;
}

const SEVERITY_RANK: Record<Severity, number> = { error: 0, warning: 1, info: 2 };

const SEVERITY_ICON: Record<Severity, typeof WarningTriangleIcon> = {
  error: XCircleIcon,
  warning: WarningTriangleIcon,
  info: InfoCircleIcon,
};

const SEVERITY_STYLE: Record<Severity, { bar: string; icon: string }> = {
  error: { bar: "border-l-error", icon: "text-error" },
  warning: { bar: "border-l-warning-bar", icon: "text-warning" },
  info: { bar: "border-l-border-strong", icon: "text-text-tertiary" },
};

/** How the association was measured, in words a reader can check. */
const METHOD_PHRASE: Record<ColumnProfile["association_method"], string> = {
  spearman: "rank association",
  eta: "eta association",
  purity: "purity association",
  none: "association",
};

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function findingsFor(profile: ProfileCard): Finding[] {
  const findings: Finding[] = [];

  for (const column of profile.columns) {
    if (column.name === profile.target_column) continue;

    if (column.flags.includes("potential_leakage")) {
      const strength =
        column.target_association !== null
          ? `a ${METHOD_PHRASE[column.association_method]} of ${column.target_association.toFixed(2)} with the target`
          : "an unusually strong relationship with the target";
      findings.push({
        column: column.name,
        severity: "error",
        text: `has ${strength} and may leak the outcome. Confirm it is knowable before prediction time.`,
      });
    }

    if (column.flags.includes("all_missing")) {
      findings.push({
        column: column.name,
        severity: "error",
        text: "is entirely empty and carries no signal at all.",
      });
    } else if (column.flags.includes("high_missing")) {
      findings.push({
        column: column.name,
        severity: "warning",
        text: `is ${pct(column.missing_pct)} empty, so any imputation will be filling in most of the column.`,
      });
    }

    if (column.flags.includes("constant")) {
      findings.push({
        column: column.name,
        severity: "warning",
        text: "holds a single value in every row, so it cannot separate anything.",
      });
    } else if (column.flags.includes("quasi_constant")) {
      findings.push({
        column: column.name,
        severity: "warning",
        text:
          column.top_value_pct !== null
            ? `is ${pct(column.top_value_pct)} one value, leaving little to learn from.`
            : "is dominated by a single value, leaving little to learn from.",
      });
    }

    if (column.flags.includes("numeric_as_string")) {
      findings.push({
        column: column.name,
        severity: "warning",
        text: `looks numeric but is stored as text (dtype ${column.pandas_dtype}). It will be treated as a category unless it is converted.`,
      });
    }

    if (column.flags.includes("id_like")) {
      findings.push({
        column: column.name,
        severity: "info",
        text: `has ${column.unique_count.toLocaleString()} distinct values across ${profile.n_rows.toLocaleString()} rows, which is identifier-shaped rather than predictive.`,
      });
    } else if (column.flags.includes("high_cardinality")) {
      findings.push({
        column: column.name,
        severity: "info",
        text: `has ${column.unique_count.toLocaleString()} distinct values, high enough that one-hot encoding it would widen the feature matrix considerably.`,
      });
    }
  }

  return findings.sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity]);
}

export function SystemWarnings({ profile }: { profile: ProfileCard }) {
  const findings = findingsFor(profile);

  if (findings.length === 0) {
    return (
      <p className="rounded-sm border border-success-border bg-success-subtle px-4 py-3 font-mono text-data-sm text-success">
        No column was flagged. Nothing needs attention before generating a strategy.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {findings.map((finding) => {
        const Icon = SEVERITY_ICON[finding.severity];
        const style = SEVERITY_STYLE[finding.severity];
        return (
          <li
            key={`${finding.column}-${finding.text}`}
            className={`flex items-start gap-3 rounded-sm border-l-2 bg-sunken px-4 py-2.5 ${style.bar}`}
          >
            <Icon className={`mt-0.5 size-4 shrink-0 ${style.icon}`} />
            <p className="text-secondary-size leading-relaxed text-text-secondary">
              <span className="font-mono text-data text-text-primary">{finding.column}</span>{" "}
              {finding.text}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
