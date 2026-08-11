/** Screen 1.5: pick the column to predict. */

import { Button } from "../components/shared/Button";
import { Card, SectionHeading } from "../components/shared/Card";
import { ColumnTable } from "../components/target/ColumnTable";
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
    <div className="mx-auto max-w-3xl">
      <div className="mb-8">
        <h2 className="text-title font-title text-text-primary">Choose what to predict</h2>
        <p className="mt-2 text-secondary-size text-text-secondary">
          <span className="font-mono">{dataset.filename}</span> &middot;{" "}
          {dataset.n_rows.toLocaleString()} rows &middot; {dataset.n_columns} columns
        </p>
      </div>

      <Card>
        <SectionHeading>Target column</SectionHeading>
        <ColumnTable columns={dataset.columns} selected={selected} onSelect={onSelect} />

        <div className="mt-5 flex items-center justify-between">
          <p className="text-caption text-text-tertiary" aria-live="polite">
            {selected ? null : "Select a column to continue."}
          </p>
          <Button onClick={onConfirm} disabled={!selected || busy} loading={busy}>
            {busy ? "Profiling dataset" : "Profile dataset"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
