/**
 * Backend client.
 *
 * Every failure path funnels through ApiError so the reducer stores one error
 * shape rather than branching on whether the server answered, the network
 * dropped, or the body failed to parse.
 */

import type {
  DatasetDetail,
  DatasetUploadResponse,
  ErrorDetail,
  ErrorResponse,
  GenerateResponse,
  ProblemType,
  ProfileResponse,
  UsageResponse,
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
      // Quote the base actually in use, not a hardcoded default. A fetch that
      // throws before producing a Response is also what a CORS rejection looks
      // like from here, so the origin is worth naming too - the two failures
      // are indistinguishable to JavaScript but have very different fixes.
      message: `Could not reach the API at ${API_BASE}. Check that the backend is running, and that it allows requests from ${window.location.origin}.`,
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

/**
 * The three members of ProblemType, at runtime.
 *
 * Needed because a React click handler wired directly to a function like
 * `onClick={handleProfile}` passes its event as the first argument, and
 * TypeScript permits that: a zero-argument function is assignable to a handler
 * that receives an event. The event then reaches JSON.stringify, which throws
 * "Converting circular structure to JSON" on the React fiber hanging off the
 * DOM node - a confusing crash a long way from its cause.
 *
 * Guarding here rather than only at the call site because the compiler cannot
 * see this class of mistake, so it will be made again.
 */
const PROBLEM_TYPES: readonly string[] = [
  "binary_classification",
  "multiclass_classification",
  "regression",
];

function asProblemType(value: unknown): ProblemType | undefined {
  return typeof value === "string" && PROBLEM_TYPES.includes(value)
    ? (value as ProblemType)
    : undefined;
}

export function profileDataset(
  datasetId: string,
  targetColumn: string,
  problemTypeOverride?: ProblemType,
): Promise<ProfileResponse> {
  const override = asProblemType(problemTypeOverride);
  return send<ProfileResponse>(`/datasets/${datasetId}/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_column: targetColumn,
      ...(override ? { problem_type_override: override } : {}),
    }),
  });
}

export function generatePipeline(
  datasetId: string,
  excludedColumns: string[] = [],
): Promise<GenerateResponse> {
  // The profile lives server side. Feature exclusions are user instructions,
  // not client-supplied facts, and the server validates every selected name.
  //
  // Same guard as profileDataset: only strings are serialised, so a click
  // event arriving here through a directly-wired handler cannot reach
  // JSON.stringify and throw on React's circular fiber references.
  const excluded = Array.isArray(excludedColumns)
    ? excludedColumns.filter((column): column is string => typeof column === "string")
    : [];
  return send<GenerateResponse>(`/datasets/${datasetId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ excluded_columns: excluded }),
  });
}

export function getDataset(datasetId: string): Promise<DatasetDetail> {
  return send<DatasetDetail>(`/datasets/${datasetId}`, { method: "GET" });
}

export function getDatasetUsage(datasetId: string): Promise<UsageResponse> {
  return send<UsageResponse>(`/datasets/${datasetId}/usage`, { method: "GET" });
}
