/** Screen 2: pick the column to predict. */

import { Button } from "../components/shared/Button";
import { Card } from "../components/shared/Card";
import { ArrowRightIcon } from "../components/shared/icons";
import { ColumnTable } from "../components/target/ColumnTable";
import { StageIntro } from "../components/layout/StageIntro";
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
    <div className="mx-auto max-w-4xl">
      <StageIntro
        stage={2}
        trail={<span className="font-mono normal-case tracking-normal text-text-secondary">{dataset.filename}</span>}
        title="What are we predicting?"
        description={<p>
          Identify the column you want the model to predict. Everything else becomes a candidate
          feature.
        </p>}
      />

      {/* The dataset facts the upload response actually returned. Mono,
          because these are values out of the file, not interface text. */}
      <dl className="mb-6 flex flex-wrap gap-x-8 gap-y-3 rounded-lg border border-border bg-surface px-5 py-4">
        {[
          { label: "Rows", value: dataset.n_rows.toLocaleString() },
          { label: "Columns", value: dataset.n_columns.toLocaleString() },
          { label: "File", value: dataset.filename },
        ].map((fact) => (
          <div key={fact.label}>
            <dt className="label-caps text-text-tertiary">{fact.label}</dt>
            <dd className="mt-1 truncate font-mono text-data text-text-primary">{fact.value}</dd>
          </div>
        ))}
      </dl>

      <Card padded={false} className="overflow-hidden">
        <ColumnTable columns={dataset.columns} selected={selected} onSelect={onSelect} />

        <div className="flex items-center justify-between gap-4 border-t border-border bg-sunken px-5 py-3">
          <p className="text-secondary-size text-text-secondary" aria-live="polite">
            {selected ? (
              <>
                Predicting <span className="font-mono text-data text-accent-ink">{selected}</span>
              </>
            ) : (
              "Select a column to continue."
            )}
          </p>
          <Button
            onClick={onConfirm}
            disabled={!selected || busy}
            loading={busy}
            iconRight={<ArrowRightIcon className="size-4" />}
          >
            {busy ? "Profiling dataset" : "Confirm target"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
