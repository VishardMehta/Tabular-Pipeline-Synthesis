/**
 * Dropped features as a real table - column name in mono, reason in prose.
 *
 * The mock adds an "Impact" column with values like "Zero Info", "High Risk"
 * and "Ignored". DroppedColumn carries exactly two fields, `column` and
 * `reason`, so that third column would have to be invented or derived by
 * keyword-matching the model's free text. Neither is a fact, so the column
 * is not here.
 */

import type { DroppedColumn } from "../../types";

export function DroppedColumnsTable({ columns }: { columns: DroppedColumn[] }) {
  if (columns.length === 0) {
    return (
      <p className="rounded-sm bg-sunken px-4 py-3 font-mono text-data-sm text-text-secondary">
        No columns were dropped. Every column is used as a feature.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-sm border border-border">
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="label-caps border-b border-border bg-sunken text-text-tertiary">
            <th className="px-4 py-2 font-bold">Column</th>
            <th className="px-4 py-2 font-bold">Reason</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((dropped) => (
            <tr key={dropped.column} className="border-b border-separator last:border-0">
              <td className="whitespace-nowrap px-4 py-2.5 align-top font-mono text-data text-accent-ink">
                {dropped.column}
              </td>
              <td className="px-4 py-2.5 text-secondary-size leading-relaxed text-text-secondary">
                {dropped.reason}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
