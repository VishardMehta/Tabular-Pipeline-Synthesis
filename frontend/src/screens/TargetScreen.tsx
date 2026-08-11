/** Screen 1.5: pick the column to predict. */

import { Button, Card, SectionTitle } from "../components/ui";
import type { DatasetUploadResponse } from "../types";

export function TargetScreen({
  dataset,
  selected,
  onSelect,
  onConfirm,
  busy,
}: {
  dataset: DatasetUploadResponse;
  selected: string | null;
  onSelect: (column: string) => void;
  onConfirm: () => void;
  busy: boolean;
}) {
  return (
    <Card>
      <SectionTitle>
        {dataset.filename} - {dataset.n_rows.toLocaleString()} rows, {dataset.n_columns} columns
      </SectionTitle>
      <p className="mb-4 text-sm text-slate-600">
        Which column should the model predict?
      </p>
      <div className="grid max-h-96 grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3">
        {dataset.columns.map((column) => (
          <button
            key={column}
            onClick={() => onSelect(column)}
            className={`truncate rounded-md border px-3 py-2 text-left text-sm transition ${
              selected === column
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-200 bg-white text-slate-700 hover:border-slate-400"
            }`}
          >
            {column}
          </button>
        ))}
      </div>
      <div className="mt-5 flex justify-end">
        <Button onClick={onConfirm} disabled={!selected || busy}>
          {busy ? "Profiling..." : "Profile dataset"}
        </Button>
      </div>
    </Card>
  );
}
