/** Screen 1: choose a CSV. */

import { useDropzone } from "react-dropzone";
import { Card } from "../components/ui";

export function UploadScreen({
  onFile,
  busy,
}: {
  onFile: (file: File) => void;
  busy: boolean;
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
    disabled: busy,
    onDrop: (files) => {
      if (files[0]) onFile(files[0]);
    },
  });

  return (
    <Card>
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-14 text-center transition ${
          isDragActive ? "border-slate-900 bg-slate-50" : "border-slate-300"
        } ${busy ? "opacity-50" : ""}`}
      >
        <input {...getInputProps()} />
        <p className="text-base font-medium text-slate-800">
          {busy ? "Uploading..." : "Drop a CSV here, or click to choose one"}
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Up to 50 MB and 1,000 columns. The file is analysed locally and never sent to the
          model.
        </p>
      </div>
    </Card>
  );
}
