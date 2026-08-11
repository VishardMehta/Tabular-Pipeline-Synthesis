import type { DroppedColumn } from "../../types";

export function DroppedColumnsTable({ columns }: { columns: DroppedColumn[] }) {
  if (columns.length === 0) {
    return <p className="text-secondary-size text-text-tertiary">No columns were dropped.</p>;
  }
  return (
    <div className="space-y-3">
      {columns.map((dropped) => (
        <div key={dropped.column} className="flex gap-4">
          <span className="w-40 shrink-0 truncate font-mono text-secondary-size font-medium text-text-primary">
            {dropped.column}
          </span>
          <p className="text-secondary-size leading-relaxed text-text-secondary">{dropped.reason}</p>
        </div>
      ))}
    </div>
  );
}
