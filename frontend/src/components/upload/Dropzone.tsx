/**
 * The upload target - the primary visual focus of screen 1.
 *
 * Constraints shown (CSV only, 50 MB, 1,000 columns) mirror
 * backend/app/heuristics.py's MAX_FILE_MB and MAX_COLS exactly. There is no
 * sample-dataset picker, which both stitch mocks show: no route in
 * app/api/datasets.py serves one, and DatasetUploadResponse has nowhere to
 * carry "which sample did you load" from a client-side fixture. That half of
 * the mock's Upload screen was cut rather than built against invented data.
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
    ? "border-error/50"
    : isDragActive
      ? "border-accent bg-accent-subtle"
      : "border-border-strong hover:border-accent hover:bg-surface-hover";

  return (
    <div
      {...getRootProps({
        // react-dropzone puts the tab stop on this element (role="presentation",
        // tabIndex 0) and tabIndex -1's the real <input> inside it, so this is
        // the element that needs the accessible name - a screen reader landing
        // on the hidden input's label alone never happens here.
        "aria-label": busy
          ? "Uploading a CSV file"
          : "Upload a CSV file. Drop a file or press enter to choose one.",
      })}
      className={`group flex min-h-[22rem] cursor-pointer flex-col items-center justify-center gap-4 rounded-lg border border-dashed bg-surface p-14 text-center transition-colors duration-150 ease-out ${borderTone} ${
        busy ? "pointer-events-none" : ""
      }`}
    >
      <input {...getInputProps()} aria-hidden="true" />

      <div
        className={`flex size-14 items-center justify-center rounded-lg transition-colors duration-150 ${
          isDragActive || busy ? "bg-accent text-text-on-accent" : "bg-accent-subtle text-accent"
        }`}
      >
        <UploadArrowIcon className="size-6" />
      </div>

      <div>
        <p className="text-title font-title text-text-primary">
          {busy ? "Uploading" : "Drop a CSV file here"}
        </p>
        {busy ? (
          // A real, thin, linear progress bar rather than a spinner. The
          // browser does not expose upload byte progress through fetch, so
          // this is deliberately indeterminate and says so - it marks that
          // work is in flight, it does not claim a percentage.
          <div
            className="progress-indeterminate relative mx-auto mt-4 h-0.5 w-48 overflow-hidden rounded-full bg-border"
            role="progressbar"
            aria-label="Upload in progress"
          />
        ) : (
          <p className="mt-2 text-body text-text-secondary">
            or <span className="font-semibold text-accent-ink underline underline-offset-2">choose a file</span>{" "}
            from your computer
          </p>
        )}
      </div>

      {!busy ? (
        <p className="mt-2 font-mono text-data-sm text-text-tertiary">
          .csv &middot; max 50 MB &middot; max 1,000 columns
        </p>
      ) : null}
    </div>
  );
}
