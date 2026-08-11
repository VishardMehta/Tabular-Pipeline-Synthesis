/**
 * The whole flow.
 *
 * One useReducer holds every piece of state in the application. No screen owns
 * state of its own, which is what stops a failed generation from taking the
 * profile down with it. See state.ts for the reducer.
 */

import { useReducer } from "react";
import { ApiError, generatePipeline, profileDataset, uploadDataset } from "./api";
import { ErrorBanner } from "./components/ui";
import { CodeScreen } from "./screens/CodeScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { StrategyScreen } from "./screens/StrategyScreen";
import { TargetScreen } from "./screens/TargetScreen";
import { UploadScreen } from "./screens/UploadScreen";
import { initialState, reducer, type Screen } from "./state";
import type { ErrorDetail } from "./types";

const STEPS: { screen: Screen; label: string }[] = [
  { screen: "upload", label: "Upload" },
  { screen: "target", label: "Target" },
  { screen: "profile", label: "Profile" },
  { screen: "strategy", label: "Strategy" },
  { screen: "code", label: "Code" },
];

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

  const activeStep = STEPS.findIndex((step) => step.screen === state.screen);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-lg font-semibold text-slate-900">Agentic AutoML</h1>
          <nav className="flex items-center gap-2 text-sm">
            {STEPS.map((step, index) => (
              <span
                key={step.screen}
                className={
                  index === activeStep
                    ? "font-medium text-slate-900"
                    : index < activeStep
                      ? "text-slate-500"
                      : "text-slate-300"
                }
              >
                {step.label}
                {index < STEPS.length - 1 ? <span className="ml-2 text-slate-300">/</span> : null}
              </span>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {state.error ? (
          <ErrorBanner
            detail={state.error}
            onRetry={state.error.retryable ? retryHandler : undefined}
            onDismiss={() => dispatch({ type: "DISMISSED_ERROR" })}
          />
        ) : null}

        {state.screen === "upload" ? (
          <UploadScreen onFile={handleUpload} busy={state.busy} />
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
      </main>
    </div>
  );
}
