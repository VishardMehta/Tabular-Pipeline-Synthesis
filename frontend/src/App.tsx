/**
 * The whole flow.
 *
 * One useReducer holds every piece of state in the application. No screen owns
 * state of its own, which is what stops a failed generation from taking the
 * profile down with it. See state.ts for the reducer.
 */

import { useReducer } from "react";
import { ApiError, generatePipeline, profileDataset, uploadDataset } from "./api";
import { ErrorPanel } from "./components/shared/ErrorPanel";
import { ProgressHeader } from "./components/layout/ProgressHeader";
import { CodeScreen } from "./screens/CodeScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { StrategyScreen } from "./screens/StrategyScreen";
import { TargetScreen } from "./screens/TargetScreen";
import { UploadScreen } from "./screens/UploadScreen";
import { initialState, reducer } from "./state";
import type { ErrorDetail } from "./types";

function toDetail(error: unknown): ErrorDetail {
  if (error instanceof ApiError) return error.detail;
  return {
    code: "UNKNOWN_ERROR",
    message: error instanceof Error ? error.message : "Something went wrong.",
    retryable: true,
    details: {},
  };
}

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);

  async function handleUpload(file: File) {
    dispatch({ type: "REQUEST_STARTED" });
    try {
      dispatch({ type: "UPLOAD_SUCCEEDED", dataset: await uploadDataset(file) });
    } catch (error) {
      dispatch({ type: "REQUEST_FAILED", error: toDetail(error) });
    }
  }

  async function handleProfile() {
    if (!state.dataset || !state.targetColumn) return;
    dispatch({ type: "REQUEST_STARTED" });
    try {
      const response = await profileDataset(state.dataset.dataset_id, state.targetColumn);
      dispatch({ type: "PROFILE_SUCCEEDED", profile: response.profile });
    } catch (error) {
      dispatch({ type: "REQUEST_FAILED", error: toDetail(error) });
    }
  }

  async function handleGenerate() {
    if (!state.dataset) return;
    dispatch({ type: "REQUEST_STARTED" });
    try {
      const response = await generatePipeline(state.dataset.dataset_id);
      dispatch({
        type: "GENERATE_SUCCEEDED",
        result: response.result,
        validation: response.validation,
      });
    } catch (error) {
      // The profile survives this. The user retries from where they were.
      dispatch({ type: "REQUEST_FAILED", error: toDetail(error) });
    }
  }

  const retryHandler =
    state.screen === "profile"
      ? handleGenerate
      : state.screen === "target"
        ? handleProfile
        : undefined;

  return (
    <div className="min-h-screen bg-bg">
      <ProgressHeader activeScreen={state.screen} datasetFilename={state.dataset?.filename} />

      <main className="mx-auto max-w-[var(--content-max-width)] px-6 py-10 sm:px-10 sm:py-14">
        {state.error ? (
          <ErrorPanel
            detail={state.error}
            onRetry={state.error.retryable ? retryHandler : undefined}
            onDismiss={() => dispatch({ type: "DISMISSED_ERROR" })}
          />
        ) : null}

        {/* Keying on screen forces a remount, which is what drives the
            screen-enter fade+translate on every navigation - section 32:
            a fade plus a small translate, never a side-slide. */}
        <div key={state.screen} className="screen-enter">
          {state.screen === "upload" ? (
            <UploadScreen onFile={handleUpload} busy={state.busy} hasError={Boolean(state.error)} />
          ) : null}

          {state.screen === "target" && state.dataset ? (
            <TargetScreen
              dataset={state.dataset}
              selected={state.targetColumn}
              onSelect={(column) => dispatch({ type: "TARGET_SELECTED", targetColumn: column })}
              onConfirm={handleProfile}
              busy={state.busy}
            />
          ) : null}

          {state.screen === "profile" && state.profile ? (
            <ProfileScreen
              profile={state.profile}
              onGenerate={handleGenerate}
              onBack={() => dispatch({ type: "NAVIGATED", screen: "target" })}
              busy={state.busy}
            />
          ) : null}

          {state.screen === "strategy" && state.result ? (
            <StrategyScreen
              result={state.result}
              onViewCode={() => dispatch({ type: "NAVIGATED", screen: "code" })}
              onBack={() => dispatch({ type: "NAVIGATED", screen: "profile" })}
            />
          ) : null}

          {state.screen === "code" && state.result && state.validation ? (
            <CodeScreen
              result={state.result}
              validation={state.validation}
              onBack={() => dispatch({ type: "NAVIGATED", screen: "strategy" })}
              onRestart={() => dispatch({ type: "RESET" })}
            />
          ) : null}
        </div>
      </main>
    </div>
  );
}
