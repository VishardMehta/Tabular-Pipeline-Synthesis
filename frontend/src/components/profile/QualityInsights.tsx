/**
 * The "DATA QUALITY INSIGHTS" chip row from the original step 3 export: one
 * compact chip per finding type, counts only, with anything at zero omitted
 * rather than listed as a zero.
 *
 * This replaces the five-row always-present list. A row reading "Constant
 * columns ......... 0" spends a line saying nothing happened; a row of chips
 * says the same thing in the space it deserves, and what is left on screen is
 * exactly what was found. The per-column detail lives in SystemWarnings
 * directly below, so nothing is lost by compressing the counts here.
 */

import { StatusBadge, type BadgeTone } from "../shared/StatusBadge";
import type { ColumnFlag, ProfileCard } from "../../types";

interface Insight {
  count: number;
  label: string;
  tone: BadgeTone;
}

function countFlag(profile: ProfileCard, flag: ColumnFlag): number {
  return profile.columns.filter((column) => column.flags.includes(flag)).length;
}

function plural(count: number, singular: string, pluralForm: string): string {
  return count === 1 ? singular : pluralForm;
}

export function QualityInsights({ profile }: { profile: ProfileCard }) {
  const leakage = countFlag(profile, "potential_leakage");
  const allMissing = countFlag(profile, "all_missing");
  const highMissing = countFlag(profile, "high_missing");
  const constant = countFlag(profile, "constant");
  const quasiConstant = countFlag(profile, "quasi_constant");
  const numericAsString = countFlag(profile, "numeric_as_string");
  const idLike = countFlag(profile, "id_like");
  const highCardinality = countFlag(profile, "high_cardinality");

  const insights: Insight[] = ([
    { count: leakage, label: `possible ${plural(leakage, "leak", "leaks")}`, tone: "error" },
    { count: allMissing, label: `empty ${plural(allMissing, "column", "columns")}`, tone: "error" },
    {
      count: highMissing,
      label: `high-missing ${plural(highMissing, "column", "columns")}`,
      tone: "warning",
    },
    {
      count: constant,
      label: `constant ${plural(constant, "column", "columns")}`,
      tone: "warning",
    },
    {
      count: quasiConstant,
      label: `quasi-constant ${plural(quasiConstant, "column", "columns")}`,
      tone: "warning",
    },
    {
      count: numericAsString,
      label: `numeric stored as text`,
      tone: "warning",
    },
    { count: idLike, label: `ID-like ${plural(idLike, "column", "columns")}`, tone: "neutral" },
    {
      count: highCardinality,
      label: `high-cardinality ${plural(highCardinality, "column", "columns")}`,
      tone: "neutral",
    },
    {
      count: profile.duplicate_row_count,
      label: `duplicate ${plural(profile.duplicate_row_count, "row", "rows")}`,
      tone: "warning",
    },
  ] satisfies Insight[]).filter((insight) => insight.count > 0);

  if (insights.length === 0) {
    return (
      <StatusBadge tone="success">
        No quality flags across {profile.n_columns} columns
      </StatusBadge>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {insights.map((insight) => (
        <StatusBadge key={insight.label} tone={insight.tone}>
          {insight.count.toLocaleString()} {insight.label}
        </StatusBadge>
      ))}
    </div>
  );
}
