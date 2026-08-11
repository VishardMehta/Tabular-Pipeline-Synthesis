/**
 * One column flag, rendered as a small semantic pill in the columns table.
 *
 * Tone follows what the flag actually means, not a uniform "warning" color
 * for everything - potential_leakage and all_missing are errors, most
 * others are advisory warnings, and id_like/high_cardinality are neutral
 * facts rather than problems (heuristics.md: "a flag is a fact with a
 * threshold behind it, never a decision").
 */

import { StatusBadge, type BadgeTone } from "../shared/StatusBadge";
import type { ColumnFlag } from "../../types";

const FLAG_TONE: Record<ColumnFlag, BadgeTone> = {
  potential_leakage: "error",
  all_missing: "error",
  high_missing: "warning",
  quasi_constant: "warning",
  constant: "warning",
  numeric_as_string: "warning",
  id_like: "neutral",
  high_cardinality: "neutral",
};

const FLAG_LABEL: Record<ColumnFlag, string> = {
  potential_leakage: "possible leakage",
  all_missing: "all missing",
  high_missing: "high missing",
  quasi_constant: "quasi-constant",
  constant: "constant",
  numeric_as_string: "numeric as string",
  id_like: "id-like",
  high_cardinality: "high cardinality",
};

export function QualityChip({ flag }: { flag: ColumnFlag }) {
  return (
    <StatusBadge tone={FLAG_TONE[flag]} icon={null}>
      {FLAG_LABEL[flag]}
    </StatusBadge>
  );
}
