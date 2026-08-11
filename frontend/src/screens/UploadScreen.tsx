/** Screen 1: choose a CSV. */

import { Dropzone } from "../components/upload/Dropzone";

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
    <div className="mx-auto max-w-2xl">
      <div className="mb-10 text-center">
        <h2 className="text-large-title font-large-title text-text-primary">
          Analyze your dataset
        </h2>
        <p className="mt-3 text-body text-text-secondary">
          Turn a CSV into an explainable ML pipeline.
        </p>
      </div>

      <Dropzone onFile={onFile} busy={busy} hasError={hasError} />
    </div>
  );
}
