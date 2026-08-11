/**
 * Hand-written mirror of backend/app/models.py.
 *
 * These types are maintained by hand and will drift from the Pydantic schemas
 * the moment someone edits one side only. Two mitigations, in order: the field
 * comments below name their Python counterpart, and once stage 0 stabilises
 * these should be generated from the OpenAPI schema at /openapi.json rather
 * than kept in sync manually.
 *
 * String union types rather than TypeScript enums throughout, because the wire
 * format is a string and a TS enum would add a runtime object for no gain.
 */

// --- Enumerations -----------------------------------------------------------

export type ProblemType =
  | "binary_classification"
  | "multiclass_classification"
  | "regression";

export type Metric =
  | "accuracy"
  | "f1"
  | "f1_macro"
  | "pr_auc"
  | "roc_auc"
  | "rmse"
  | "mae"
  | "r2";

export type InferredType =
  | "boolean"
  | "datetime"
  | "numeric_discrete"
  | "numeric_continuous"
  | "categorical"
  | "text"
  | "unknown";

export type ColumnFlag =
  | "all_missing"
  | "high_missing"
  | "constant"
  | "quasi_constant"
  | "id_like"
  | "high_cardinality"
  | "numeric_as_string"
  | "potential_leakage";

export type ValidationSeverity = "error" | "warning" | "info";

export type JobState =
  | "pending"
  | "profiling"
  | "generating"
  | "validating"
  | "complete"
  | "failed";

// --- Profiling --------------------------------------------------------------

export interface ColumnProfile {
  name: string;
  inferred_type: InferredType;
  pandas_dtype: string;
  missing_count: number;
  missing_pct: number;
  unique_count: number;
  unique_pct: number;
  top_value_pct: number | null;
  /** Level names, categoricals of 20 or fewer levels only, max 5 entries. */
  sample_values: string[] | null;
  min: number | null;
  max: number | null;
  mean: number | null;
  std: number | null;
  median: number | null;
  parse_rate: number | null;
  target_association: number | null;
  flags: ColumnFlag[];
}

export interface ProfileCard {
  dataset_id: string;
  filename: string;
  n_rows: number;
  n_columns: number;
  target_column: string;
  problem_type: ProblemType;
  task_confidence: number;
  primary_metric: Metric;
  /** Always populated. Rendering the primary alone hides how it was chosen. */
  secondary_metrics: Metric[];
  class_balance_ratio: number | null;
  duplicate_row_count: number;
  profiled_on_sample: boolean;
  sample_rows: number | null;
  columns: ColumnProfile[];
}

// --- Generation result ------------------------------------------------------

export interface DroppedColumn {
  column: string;
  reason: string;
}

export interface PreprocessingStep {
  step: string;
  columns: string[];
  rationale: string;
}

export interface CandidateModel {
  name: string;
  library: string;
  rationale: string;
}

/**
 * Mirrors GenResult. The field order below matches the Python declaration
 * order, which is load-bearing on the backend. It carries no score field of any
 * kind and must never gain one: MVP-1 does not execute the generated code, so
 * any number rendered as a result would be fabricated.
 */
export interface GenResult {
  problem_type: ProblemType;
  target_column: string;
  primary_metric: Metric;
  dropped_columns: DroppedColumn[];
  preprocessing: PreprocessingStep[];
  candidate_models: CandidateModel[];
  validation_strategy: string;
  analysis_summary: string;
  risks: string[];
  code: string;
}

// --- Validation -------------------------------------------------------------

export interface ValidationCheck {
  check_id: string;
  title: string;
  severity: ValidationSeverity;
  passed: boolean;
  message: string;
  details: string[];
}

export interface ValidationReport {
  passed: boolean;
  error_count: number;
  warning_count: number;
  checks: ValidationCheck[];
}

// --- Error envelope ---------------------------------------------------------

export interface ErrorDetail {
  code: string;
  message: string;
  retryable: boolean;
  details: Record<string, string>;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

// --- API bodies -------------------------------------------------------------

export interface DatasetUploadResponse {
  dataset_id: string;
  filename: string;
  n_rows: number;
  n_columns: number;
  columns: string[];
  state: JobState;
}

export interface ProfileRequest {
  target_column: string;
}

export interface ProfileResponse {
  state: JobState;
  profile: ProfileCard;
}

export interface GenerateResponse {
  state: JobState;
  result: GenResult;
  validation: ValidationReport;
}

export interface HealthResponse {
  status: string;
  version: string;
}
