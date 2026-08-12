/**
 * The one piece of flow state in the application.
 *
 * Every screen reads from this object and none of them hold state of their own.
 * That is the whole point: with per-screen state, a failed generation unmounts
 * the strategy screen and takes the profile with it, and the user has to
 * re-upload to get back to where they were. Here a failure sets `error` and
 * leaves `profile` untouched, so retrying costs one click.
 *
 * The reducer lives here rather than in App.tsx so it can be read and tested
 * without the component around it. The single useReducer call is in App.tsx.
 */

import type {
  DatasetUploadResponse,
  DatasetDetail,
  ErrorDetail,
  GenResult,
  ProblemType,
  ProfileCard,
  UsageResponse,
  ValidationReport,
} from "./types";

export type Screen = "landing" | "upload" | "target" | "profile" | "strategy" | "code";
export type Operation = "upload" | "profile" | "generate" | null;

export interface AppState {
  screen: Screen;
  busy: boolean;
  operation: Operation;
  profileOverride: ProblemType | null;
  error: ErrorDetail | null;
  dataset: DatasetUploadResponse | null;
  targetColumn: string | null;
  profile: ProfileCard | null;
  result: GenResult | null;
  validation: ValidationReport | null;
  excludedColumns: string[];
  taskWasOverridden: boolean;
  usage: UsageResponse | null;
}

export const initialState: AppState = {
  screen: "landing",
  busy: false,
  operation: null,
  profileOverride: null,
  error: null,
  dataset: null,
  targetColumn: null,
  profile: null,
  result: null,
  validation: null,
  excludedColumns: [],
  taskWasOverridden: false,
  usage: null,
};

export type Action =
  | {
      type: "REQUEST_STARTED";
      operation: Exclude<Operation, null>;
      profileOverride?: ProblemType;
    }
  | { type: "REQUEST_FAILED"; error: ErrorDetail }
  | { type: "UPLOAD_SUCCEEDED"; dataset: DatasetUploadResponse }
  | { type: "TARGET_SELECTED"; targetColumn: string }
  | { type: "PROFILE_SUCCEEDED"; profile: ProfileCard; taskWasOverridden: boolean }
  | { type: "GENERATE_SUCCEEDED"; result: GenResult; validation: ValidationReport; usage: UsageResponse | null }
  | { type: "EXCLUSIONS_CHANGED"; columns: string[] }
  | { type: "SESSION_RESTORED"; dataset: DatasetDetail }
  | { type: "NAVIGATED"; screen: Screen }
  | { type: "DISMISSED_ERROR" }
  | { type: "RESET" };

export function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "REQUEST_STARTED":
      return {
        ...state,
        busy: true,
        operation: action.operation,
        profileOverride: action.operation === "profile" ? action.profileOverride ?? null : state.profileOverride,
        error: null,
      };

    case "REQUEST_FAILED":
      // Note what is absent: nothing is cleared. A generation that fails leaves
      // the profile in place so the retry does not restart the flow.
      return { ...state, busy: false, error: action.error };

    case "UPLOAD_SUCCEEDED":
      return {
        ...initialState,
        dataset: action.dataset,
        screen: "target",
      };

    case "TARGET_SELECTED":
      return {
        ...state,
        targetColumn: action.targetColumn,
        profile: null,
        result: null,
        validation: null,
        usage: null,
        excludedColumns: [],
        taskWasOverridden: false,
        error: null,
      };

    case "PROFILE_SUCCEEDED":
      return {
        ...state,
        busy: false,
        operation: null,
        profileOverride: null,
        error: null,
        profile: action.profile,
        result: null,
        validation: null,
        usage: null,
        taskWasOverridden: action.taskWasOverridden,
        screen: "profile",
      };

    case "GENERATE_SUCCEEDED":
      return {
        ...state,
        busy: false,
        operation: null,
        profileOverride: null,
        error: null,
        result: action.result,
        validation: action.validation,
        usage: action.usage,
        screen: "strategy",
      };

    case "EXCLUSIONS_CHANGED":
      return { ...state, excludedColumns: action.columns };

    case "SESSION_RESTORED":
      return {
        ...initialState,
        dataset: {
          dataset_id: action.dataset.dataset_id,
          filename: action.dataset.filename,
          n_rows: action.dataset.n_rows,
          n_columns: action.dataset.n_columns,
          columns: action.dataset.columns,
          state: action.dataset.state,
        },
        targetColumn: action.dataset.profile?.target_column ?? null,
        profile: action.dataset.profile,
        taskWasOverridden: action.dataset.task_was_overridden,
        screen: action.dataset.profile ? "profile" : "target",
      };

    case "NAVIGATED":
      return { ...state, screen: action.screen, error: null };

    case "DISMISSED_ERROR":
      return { ...state, error: null };

    case "RESET":
      return initialState;
  }
}
