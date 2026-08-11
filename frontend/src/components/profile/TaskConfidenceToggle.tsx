/**
 * task_confidence as a two-state badge - section 20 lists "HIGH CONFIDENCE"
 * and "AMBIGUOUS" as exactly this kind of status label.
 *
 * Placed on the Profile screen, not Target selection. task_confidence does
 * not exist until POST /profile returns - DatasetUploadResponse carries only
 * column names, nothing about inferred type or task. Both HTML exports show
 * this on the target-picker screen; that would mean fabricating a number
 * the API has not computed yet, which is the one rule in this brief that is
 * not a style choice.
 *
 * The threshold (0.85) is a display decision, not a backend one: today the
 * profiler only ever emits 0.95 (TASK_CONFIDENCE_TYPE_MATCH) or 0.65
 * (TASK_CONFIDENCE_DISCRETE_AMBIGUOUS), so anywhere comfortably between
 * those two values draws the same line without hardcoding either constant.
 */

import { StatusBadge } from "../shared/StatusBadge";

const HIGH_CONFIDENCE_THRESHOLD = 0.85;

export function TaskConfidenceToggle({ confidence }: { confidence: number }) {
  const isHigh = confidence >= HIGH_CONFIDENCE_THRESHOLD;
  return (
    <StatusBadge tone={isHigh ? "success" : "warning"}>
      {isHigh ? "High confidence" : "Ambiguous - verify the task"}
    </StatusBadge>
  );
}
