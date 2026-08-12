import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Check, Circle, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import type { Operation } from "../../state";
import logo from "../../assets/autonexus-logo.png";

const activityByOperation: Record<Exclude<Operation, null>, { title: string; body: string; steps: string[] }> = {
  upload: {
    title: "Bringing in your dataset",
    body: "We are reading the CSV and checking that its shape is supported.",
    steps: ["Upload request sent", "Waiting for dataset summary", "Opening target selection"],
  },
  profile: {
    title: "Building the data profile",
    body: "Python is computing the facts that will ground the strategy.",
    steps: ["Target selection sent", "Waiting for the computed profile", "Opening your data profile"],
  },
  generate: {
    title: "Writing a grounded strategy",
    body: "The model is reasoning over the computed profile, then the returned code is statically checked.",
    steps: ["Generation request sent", "Waiting for strategy and validation", "Opening the generated plan"],
  },
};

type ActivityPhase = "working" | "handoff";

export function ActivityDialog({
  operation,
  open,
  phase,
}: {
  operation: Operation;
  open: boolean;
  phase: ActivityPhase;
}) {
  const reducedMotion = useReducedMotion();
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!open) {
      setElapsedSeconds(0);
      return;
    }
    const startedAt = Date.now();
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 250);
    return () => window.clearInterval(timer);
  }, [open, operation]);

  if (!operation) return null;
  const activity = activityByOperation[operation];
  const activeStep = phase === "working" ? 1 : activity.steps.length - 1;

  function stepState(index: number) {
    if (index < activeStep) return "done";
    if (index === activeStep) return "active";
    return "waiting";
  }

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="activity-overlay"
          role="status"
          aria-live="polite"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reducedMotion ? 0.01 : 0.2 }}
        >
          <motion.section
            className="activity-dialog"
            initial={{ opacity: 0, y: reducedMotion ? 0 : 18, scale: reducedMotion ? 1 : 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: reducedMotion ? 0 : 8 }}
            transition={{ duration: reducedMotion ? 0.01 : 0.36, ease: "easeOut" }}
          >
            <div className="activity-dialog__top">
              <div className="activity-dialog__signal"><img src={logo} alt="" /></div>
              <div>
                <p className="label-caps text-accent-ink">AutoNexus is working</p>
                <div className="activity-dialog__live">
                  <span aria-hidden /> {phase === "handoff" ? "Response received" : `Live request · ${elapsedSeconds}s`}
                </div>
              </div>
            </div>
            <h2>{activity.title}</h2>
            <p>{activity.body}</p>
            <div className={`activity-dialog__indeterminate activity-dialog__indeterminate--${phase}`} aria-hidden><span /></div>
            <p className="activity-dialog__list-label">
              {phase === "handoff" ? "Response ready" : "Work in this request"}
            </p>
            <ol>
              {activity.steps.map((step, index) => (
                <li key={step} className={`activity-dialog__step--${stepState(index)}`}>
                  <span className="activity-dialog__step-icon">
                    {stepState(index) === "done" ? <Check className="size-3.5" strokeWidth={2.8} /> : stepState(index) === "active" ? <LoaderCircle className="size-3.5 animate-spin" /> : <Circle className="size-3.5" />}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
            <div className="activity-dialog__rule">
              <span /> {phase === "handoff" ? "The server response is ready. Opening the next stage." : "This window stays open until the server responds."}
            </div>
          </motion.section>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
