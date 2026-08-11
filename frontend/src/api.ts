/**
 * Backend client.
 *
 * Every failure path funnels through ApiError so the reducer stores one error
 * shape rather than branching on whether the server answered, the network
 * dropped, or the body failed to parse.
 */

import type {
  DatasetUploadResponse,
  ErrorDetail,
  ErrorResponse,
  GenerateResponse,
  ProfileResponse,
} from "./types";

// Overridable because port 8000 is a popular default and collides often. Set
// VITE_API_BASE in frontend/.env.local, and keep CORS_ORIGINS on the backend in
// step with wherever the dev server ends up.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

export class ApiError extends Error {
  readonly detail: ErrorDetail;

  constructor(detail: ErrorDetail) {
    super(detail.message);
    this.name = "ApiError";
    this.detail = detail;
  }
}

async function unwrap<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }
  // The backend envelopes every non-2xx body as {error: ErrorDetail}. Anything
  // else reaching here came from a proxy or a crash, so synthesise a detail
  // rather than let the caller see a parse error.
  let detail: ErrorDetail = {
    code: "UNEXPECTED_RESPONSE",
    message: `The server returned ${response.status}.`,
    retryable: response.status >= 500,
    details: {},
  };
  try {
    const body = (await response.json()) as ErrorResponse;
    if (body?.error?.code) {
      detail = body.error;
    }
  } catch {
    // Keep the synthesised detail.
  }
  throw new ApiError(detail);
}

async function send<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError({
      code: "NETWORK_ERROR",
      message: "Could not reach the API. Check that the backend is running on port 8000.",
      retryable: true,
      details: {},
    });
  }
  return unwrap<T>(response);
}

export function uploadDataset(file: File): Promise<DatasetUploadResponse> {
  const body = new FormData();
  body.append("file", file);
  return send<DatasetUploadResponse>("/datasets", { method: "POST", body });
}

export function profileDataset(
  datasetId: string,
  targetColumn: string,
): Promise<ProfileResponse> {
  return send<ProfileResponse>(`/datasets/${datasetId}/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_column: targetColumn }),
  });
}

export function generatePipeline(datasetId: string): Promise<GenerateResponse> {
  // Empty body on purpose. The profile lives server side; sending it would let
  // the client rewrite the facts the model reasons over.
  return send<GenerateResponse>(`/datasets/${datasetId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
}
