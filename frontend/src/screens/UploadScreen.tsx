/** Screen 1: choose a CSV. */

import { Dropzone } from "../components/upload/Dropzone";
import { CheckCircleIcon, InfoCircleIcon } from "../components/shared/icons";
import { StageIntro } from "../components/layout/StageIntro";

/**
 * Requirements the backend genuinely enforces, each traceable to a real
 * constant or code path in backend/app: MAX_FILE_MB and MAX_COLS in
 * heuristics.py, the header-row read in ingest.py, and the target column the
 * next screen asks for. Nothing aspirational.
 */
const REQUIREMENTS: { title: string; body: string }[] = [
  {
    title: "Tabular CSV",
    body: "One row per observation, one column per feature. Read with the pandas C engine.",
  },
  {
    title: "Header row",
    body: "The first row must hold the column names. They are read verbatim, so keep them unique.",
  },
  {
    title: "A target column",
    body: "One column you want to predict. You pick it on the next screen, not here.",
  },
];

export function UploadScreen({
  onFile,
  busy,
  hasError,
}: {
  onFile: (file: File) => void;
  busy: boolean;
  hasError?: boolean;
}) {
  return (
    <div>
      <StageIntro
        stage={1}
        title="Drop in the data."
        description={
          <p>
          Provide a CSV to begin. It is profiled in Python, and only the resulting statistics are
          sent to the model - never the rows themselves.
          </p>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <Dropzone onFile={onFile} busy={busy} hasError={hasError} />

        <aside className="rounded-lg border border-border bg-surface p-6">
          <h3 className="mb-4 text-heading font-heading text-text-primary">Data requirements</h3>
          <ul className="space-y-4">
            {REQUIREMENTS.map((item) => (
              <li key={item.title} className="flex gap-3">
                <CheckCircleIcon className="mt-0.5 size-4 shrink-0 text-accent" />
                <div>
                  <p className="text-secondary-size font-semibold text-text-primary">{item.title}</p>
                  <p className="mt-1 font-mono text-data-sm leading-relaxed text-text-secondary">
                    {item.body}
                  </p>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-6 border-t border-separator pt-5">
            <p className="label-caps mb-2 flex items-center gap-2 text-text-tertiary">
              <InfoCircleIcon className="size-3.5" />
              Where your data goes
            </p>
            <p className="font-mono text-data-sm leading-relaxed text-text-secondary">
              The file is stored on this server and profiled locally. The model receives the profile
              card only: column names, types, and summary statistics.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
