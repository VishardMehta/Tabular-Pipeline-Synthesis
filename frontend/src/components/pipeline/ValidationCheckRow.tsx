/**
 * One row of a real ValidationReport.checks entry - never a hand-picked
 * subset. check_id, title, severity, message and details all come straight
 * from validation.py; nothing here is invented. In particular there is no
 * "Security Scan (Bandit)" or "Type Checking (MyPy)" row, which the stitch
 * mock shows - those checks do not exist in this system.
 *
 * Structure and motion are adapted from the `agent-plan` component: a
 * collapsible row whose status icon cross-fades on change, with the detail
 * list revealed underneath against a dashed connector rail. What is NOT
 * adapted is its data model - that component ships hardcoded tasks and a
 * `toggleTaskStatus` that assigns `statuses[Math.floor(Math.random() * ...)]`.
 * Status here is derived from `check.passed` and `check.severity` and is not
 * settable at all, because a static check's outcome is a fact about the
 * generated code, not something a reader can toggle.
 *
 * Rows are collapsed by default and expand to show `details`. A check with no
 * details is not expandable, and says so by not offering the affordance.
 */

import { useId, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  CircleX,
  Info,
  type LucideIcon,
} from "lucide-react";
import type { ValidationCheck } from "../../types";

// The source component hardcodes its easing inline in six places. One curve,
// named once - the same "settle" feel, applied consistently.
const EASE_SETTLE = [0.2, 0.65, 0.3, 0.9] as const;

interface RowTone {
  icon: LucideIcon;
  color: string;
  label: string;
}

function rowTone(check: ValidationCheck): RowTone {
  if (check.passed) return { icon: CheckCircle2, color: "text-success", label: "Passed" };
  if (check.severity === "error") return { icon: CircleX, color: "text-error", label: "Error" };
  if (check.severity === "warning")
    return { icon: CircleAlert, color: "text-warning", label: "Warning" };
  return { icon: Info, color: "text-text-tertiary", label: "Info" };
}

export function ValidationCheckRow({
  check,
  index,
  reducedMotion,
}: {
  check: ValidationCheck;
  index: number;
  reducedMotion: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const detailsId = useId();
  const { icon: Icon, color, label } = rowTone(check);
  const expandable = check.details.length > 0;

  return (
    <li className="border-b border-separator last:border-0">
      <motion.div
        initial={reducedMotion ? false : { opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          duration: 0.25,
          // Capped so a twelve-row report never feels slow to finish arriving.
          delay: reducedMotion ? 0 : Math.min(index, 10) * 0.028,
          ease: EASE_SETTLE,
        }}
      >
        <div className="flex gap-3 px-5 py-3">
          {/* The icon cross-fades when the status changes. It is presentation
              only: unlike the source component this is not a button, because
              there is nothing here a click could legitimately change. */}
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={`${check.check_id}-${label}`}
              initial={reducedMotion ? false : { opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2, ease: EASE_SETTLE }}
              className={`mt-0.5 shrink-0 ${color}`}
            >
              <Icon className="size-4" strokeWidth={1.75} aria-hidden />
            </motion.span>
          </AnimatePresence>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
              <p className="text-secondary-size font-semibold text-text-primary">{check.title}</p>
              {/* The word, not only the icon colour, so the state survives
                  greyscale and colour-blindness. */}
              <span className={`label-caps ${color}`}>{label}</span>
            </div>
            <p className="mt-1 text-secondary-size leading-relaxed text-text-secondary">
              {check.message}
            </p>

            {expandable ? (
              <button
                type="button"
                onClick={() => setExpanded((open) => !open)}
                aria-expanded={expanded}
                aria-controls={detailsId}
                className="mt-2 inline-flex items-center gap-1 rounded-sm text-text-tertiary transition-colors hover:text-accent-ink"
              >
                <motion.span
                  animate={{ rotate: expanded ? 90 : 0 }}
                  transition={{ duration: reducedMotion ? 0 : 0.2, ease: EASE_SETTLE }}
                  className="flex"
                >
                  <ChevronRight className="size-3.5" strokeWidth={2} aria-hidden />
                </motion.span>
                <span className="label-caps">
                  {check.details.length} {check.details.length === 1 ? "detail" : "details"}
                </span>
              </button>
            ) : null}
          </div>
        </div>
      </motion.div>

      <AnimatePresence initial={false}>
        {expanded ? (
          <motion.div
            id={detailsId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: reducedMotion ? 0 : 0.25, ease: EASE_SETTLE }}
            className="overflow-hidden"
          >
            {/* The dashed rail from the source component, aligned under the
                status icon so the details read as belonging to this check. */}
            <ul className="ml-[2.05rem] mr-5 mb-3 space-y-1 border-l border-dashed border-border-strong pl-4">
              {check.details.map((detail, detailIndex) => (
                <motion.li
                  key={detail}
                  initial={reducedMotion ? false : { opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    duration: 0.2,
                    delay: reducedMotion ? 0 : detailIndex * 0.04,
                    ease: EASE_SETTLE,
                  }}
                  className="font-mono text-data-sm leading-relaxed text-text-tertiary"
                >
                  {detail}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </li>
  );
}
