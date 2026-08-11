/**
 * The application shell's top bar and step indicator.
 *
 * No permanent sidebar. Section 9: "do not force a sidebar if the current
 * workflow is linear... for the initial upload experience, a centered
 * full-width composition is better." This workflow has no branching
 * navigation, no history, and no workspace concept in the real API - it is
 * exactly the linear case the doc describes, so the shell stays a quiet top
 * bar with a compact step indicator (section 11), not five glowing circles
 * and not a 280px rail for five sequential screens.
 */

import { CheckCircleIcon, ChevronRightIcon } from "../shared/icons";
import type { Screen } from "../../state";

export const STEPS: { screen: Screen; label: string }[] = [
  { screen: "upload", label: "Upload" },
  { screen: "target", label: "Target" },
  { screen: "profile", label: "Profile" },
  { screen: "strategy", label: "Strategy" },
  { screen: "code", label: "Pipeline" },
];

function StepItem({
  index,
  label,
  state,
}: {
  index: number;
  label: string;
  state: "done" | "current" | "upcoming";
}) {
  return (
    <div className="flex items-center gap-1.5">
      {state === "done" ? (
        <CheckCircleIcon className="size-4 text-success" />
      ) : (
        <span
          className={`flex size-4 items-center justify-center rounded-full text-[10px] font-semibold ${
            state === "current"
              ? "bg-accent text-text-on-accent"
              : "bg-surface-secondary text-text-tertiary"
          }`}
        >
          {index + 1}
        </span>
      )}
      <span
        className={`text-secondary-size ${
          state === "current"
            ? "font-medium text-text-primary"
            : state === "done"
              ? "text-text-secondary"
              : "text-text-tertiary"
        }`}
      >
        {label}
      </span>
    </div>
  );
}

export function ProgressHeader({
  activeScreen,
  datasetFilename,
}: {
  activeScreen: Screen;
  datasetFilename?: string | null;
}) {
  const activeIndex = STEPS.findIndex((step) => step.screen === activeScreen);

  return (
    <header className="sticky top-0 z-10 border-b border-separator bg-surface/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-[var(--content-max-width)] items-center justify-between gap-6 px-6 py-4 sm:px-10">
        <div className="flex min-w-0 items-center gap-3">
          <h1 className="shrink-0 text-secondary-size font-semibold text-text-primary">
            Agentic AutoML
          </h1>
          {datasetFilename ? (
            <>
              <span className="text-text-tertiary" aria-hidden>
                /
              </span>
              <span className="truncate font-mono text-caption text-text-secondary">
                {datasetFilename}
              </span>
            </>
          ) : null}
        </div>

        <nav aria-label="Workflow progress" className="hidden items-center gap-3 md:flex">
          {STEPS.map((step, index) => (
            <div key={step.screen} className="flex items-center gap-3">
              {index > 0 ? <ChevronRightIcon className="size-3 text-separator" /> : null}
              <StepItem
                index={index}
                label={step.label}
                state={index < activeIndex ? "done" : index === activeIndex ? "current" : "upcoming"}
              />
            </div>
          ))}
        </nav>

        {/* Compact fallback below the md breakpoint: current step only. */}
        <p className="text-caption text-text-tertiary md:hidden">
          Step {activeIndex + 1} of {STEPS.length} &middot; {STEPS[activeIndex]?.label}
        </p>
      </div>
    </header>
  );
}
