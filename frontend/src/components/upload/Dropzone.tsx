/**
 * The upload target - section 43: "should be the primary visual focus."
 *
 * Constraints shown (CSV only, 50 MB, 1,000 columns) mirror
 * backend/app/heuristics.py's MAX_FILE_MB and MAX_COLS exactly. There is no
 * sample-dataset picker here: no route in app/api/datasets.py serves one,
 * and DatasetUploadResponse has nowhere to carry the answer to "which
 * sample did you load" from a client-side fixture. See the stage report for
 * why that half of both HTML exports' Upload screen was cut rather than
 * built against invented data.
 */

import { useDropzone } from "react-dropzone";
import { UploadArrowIcon } from "../shared/icons";

export function Dropzone({
  onFile,
  busy,
  hasError,
}: {
  onFile: (file: File) => void;
  busy: boolean;
  hasError?: boolean;
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
    disabled: busy,
    onDrop: (files) => {
      if (files[0]) onFile(files[0]);
    },
  });

  const borderTone = hasError
    ? "border-error/60"
    : isDragActive
      ? "border-accent bg-accent-subtle"
      : "border-border hover:border-text-tertiary";

  return (
    <div
      {...getRootProps({
        // react-dropzone puts the tab stop on this element (role="presentation",
        // tabIndex 0) and tabIndex -1's the real <input> inside it, so this is
        // the element that needs the accessible name - a screen reader
        // landing on the hidden input's label alone never happens here.
        "aria-label": busy
          ? "Uploading a CSV file"
          : "Upload a CSV file. Drop a file or press enter to choose one.",
      })}
      className={`group flex min-h-64 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-14 text-center transition-colors duration-150 ease-out ${borderTone} ${
        busy ? "pointer-events-none opacity-60" : ""
      }`}
    >
      <input {...getInputProps()} aria-hidden="true" />

      <div
        className={`flex size-12 items-center justify-center rounded-full transition-colors duration-150 ${
          isDragActive ? "bg-accent text-text-on-accent" : "bg-surface-secondary text-text-secondary"
        }`}
      >
        <UploadArrowIcon className="size-5" />
      </div>

      <p className="text-heading font-heading text-text-primary">
        {busy ? "Uploading" : "Drop a CSV file here"}
      </p>
      {!busy ? (
        <p className="text-secondary-size text-accent">
          or <span className="underline underline-offset-2">choose a file</span>
        </p>
      ) : null}
      <p className="font-mono text-caption text-text-tertiary">CSV only &middot; max 50 MB &middot; max 1,000 columns</p>
    </div>
  );
}
