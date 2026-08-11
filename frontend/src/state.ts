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
  ErrorDetail,
  GenResult,
  ProfileCard,
  ValidationReport,
} from "./types";

export type Screen = "upload" | "target" | "profile" | "strategy" | "code";

export interface AppState {
  screen: Screen;
  busy: boolean;
  error: ErrorDetail | null;
  dataset: DatasetUploadResponse | null;
  targetColumn: string | null;
  profile: ProfileCard | null;
  result: GenResult | null;
  validation: ValidationReport | null;
}

export const initialState: AppState = {
  screen: "upload",
  busy: false,
  error: null,
  dataset: null,
  targetColumn: null,
  profile: null,
  result: null,
  validation: null,
};

export type Action =
  | { type: "REQUEST_STARTED" }
  | { type: "REQUEST_FAILED"; error: ErrorDetail }
  | { type: "UPLOAD_SUCCEEDED"; dataset: DatasetUploadResponse }
  | { type: "TARGET_SELECTED"; targetColumn: string }
  | { type: "PROFILE_SUCCEEDED"; profile: ProfileCard }
  | { type: "GENERATE_SUCCEEDED"; result: GenResult; validation: ValidationReport }
  | { type: "NAVIGATED"; screen: Screen }
  | { type: "DISMISSED_ERROR" }
  | { type: "RESET" };

export function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "REQUEST_STARTED":
      return { ...state, busy: true, error: null };

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
      return { ...state, targetColumn: action.targetColumn, error: null };

    case "PROFILE_SUCCEEDED":
      return {
        ...state,
        busy: false,
        error: null,
        profile: action.profile,
        screen: "profile",
      };

    case "GENERATE_SUCCEEDED":
      return {
        ...state,
        busy: false,
        error: null,
        result: action.result,
        validation: action.validation,
        screen: "strategy",
      };

    case "NAVIGATED":
      return { ...state, screen: action.screen, error: null };

    case "DISMISSED_ERROR":
      return { ...state, error: null };

    case "RESET":
      return initialState;
  }
}
