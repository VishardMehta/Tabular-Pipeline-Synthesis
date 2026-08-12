/** Screen 3: the computed facts. Every number here came from Python. */

import { Button } from "../components/shared/Button";
import { Card, CardHeader } from "../components/shared/Card";
import { ArrowRightIcon, ChevronLeftIcon } from "../components/shared/icons";
import { ClassBalanceChart } from "../components/profile/ClassBalanceChart";
import { MetricPanel } from "../components/profile/MetricPanel";
import { QualityChip } from "../components/profile/QualityChip";
import { QualityInsights } from "../components/profile/QualityInsights";
import { SystemWarnings } from "../components/profile/SystemWarnings";
import { StatTile } from "../components/profile/StatTile";
import { TaskConfidenceToggle } from "../components/profile/TaskConfidenceToggle";
import { DataTag } from "../components/shared/StatusBadge";
import { StageIntro } from "../components/layout/StageIntro";
import type { ColumnFlag, ProblemType, ProfileCard } from "../types";

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const PROBLEM_LABEL: Record<ProfileCard["problem_type"], string> = {
  binary_classification: "Binary classification",
  multiclass_classification: "Multiclass classification",
  regression: "Regression",
};

function countFlag(profile: ProfileCard, flag: ColumnFlag): number {
  return profile.columns.filter((column) => column.flags.includes(flag)).length;
}

function averageMissing(profile: ProfileCard): number {
  if (profile.columns.length === 0) return 0;
  return profile.columns.reduce((sum, column) => sum + column.missing_pct, 0) / profile.columns.length;
}

export function ProfileScreen({
  profile,
  onGenerate,
  excludedColumns,
  onExclusionsChange,
  onOverrideTask,
  taskWasOverridden,
  onBack,
  busy,
}: {
  profile: ProfileCard;
  onGenerate: () => void;
  excludedColumns: string[];
  onExclusionsChange: (columns: string[]) => void;
  onOverrideTask: (problemType: ProblemType) => void;
  taskWasOverridden: boolean;
  onBack: () => void;
  busy: boolean;
}) {
  const targetColumn = profile.columns.find((column) => column.name === profile.target_column);
  const highMissingCount = countFlag(profile, "high_missing");
  const avgMissing = averageMissing(profile);
  const duplicateShare = profile.n_rows > 0 ? profile.duplicate_row_count / profile.n_rows : 0;
  const featureColumns = profile.columns.filter((column) => column.name !== profile.target_column);

  function toggleExclusion(columnName: string) {
    const next = excludedColumns.includes(columnName)
      ? excludedColumns.filter((column) => column !== columnName)
      : [...excludedColumns, columnName];
    onExclusionsChange(next);
  }

  return (
    <div className="space-y-6">
      <StageIntro
        stage={3}
        trail={<span className="font-mono normal-case tracking-normal text-text-secondary">{profile.target_column}</span>}
        title="Here is what your data is telling us."
        description={<p className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span>Computed facts for target</span>
          <span className="rounded-tag bg-accent-subtle px-2 py-0.5 font-mono text-data text-accent-ink">
            {profile.target_column}
          </span>
        </p>}
      />
      <div>
        {profile.profiled_on_sample ? (
          // Disclosed whenever true, never quietly. The reader needs to know
          // these statistics describe a sample, not the whole file.
          <p className="mt-3 inline-flex items-center gap-2 rounded-sm border border-warning-border bg-warning-subtle px-3 py-1.5 font-mono text-data-sm text-warning">
            Profiled on a {profile.sample_rows?.toLocaleString()}-row sample of{" "}
            {profile.n_rows.toLocaleString()} rows.
          </p>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile label="Total rows" value={profile.n_rows.toLocaleString()} />
        <StatTile label="Total columns" value={profile.n_columns.toLocaleString()} />
        <StatTile
          label="Duplicate rows"
          value={profile.duplicate_row_count.toLocaleString()}
          note={profile.duplicate_row_count > 0 ? `(${pct(duplicateShare)})` : undefined}
          tone={profile.duplicate_row_count > 0 ? "warning" : "neutral"}
          toneLabel="Warning: duplicate rows present"
        />
        <StatTile
          label="Missing values"
          value={pct(avgMissing)}
          note="avg/col"
          tone={highMissingCount > 0 ? "error" : avgMissing > 0 ? "warning" : "neutral"}
          toneLabel={
            highMissingCount > 0
              ? "Error: columns above the high-missing threshold"
              : "Warning: some values are missing"
          }
        />
      </div>

      {/* items-start so the metric panel sizes to its own content. Stretching
          it to the full height of the left column leaves a large empty blue
          field under the rationale, which reads as a rendering fault rather
          than as emphasis. */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] lg:items-start">
        <div className="space-y-6">
          <Card>
            <CardHeader title="Target and task analysis" />
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <p className="label-caps mb-2 text-text-tertiary">Target variable</p>
                <span className="inline-block rounded-tag bg-accent-subtle px-2 py-1 font-mono text-data text-accent-ink">
                  {profile.target_column}
                </span>
              </div>
              <div>
                <p className="label-caps mb-2 text-text-tertiary">Inferred task</p>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-body text-text-primary">
                    {PROBLEM_LABEL[profile.problem_type]}
                  </span>
                  <TaskConfidenceToggle confidence={profile.task_confidence} />
                  {taskWasOverridden ? (
                    <span className="rounded-tag border border-accent/30 bg-accent-subtle px-2 py-0.5 font-mono text-data-sm text-accent-ink">
                      selected by you
                    </span>
                  ) : null}
                </div>
              </div>
            </div>

            {profile.task_confidence < 0.85 && !taskWasOverridden ? (
              <div className="mt-6 border-t border-separator pt-5">
                <p className="label-caps text-text-tertiary">Task decision</p>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-4">
                  <p className="max-w-xl text-body-sm leading-relaxed text-text-secondary">
                    This discrete numeric target could also represent a continuous outcome. Keep the inferred task, or set it to regression before generating.
                  </p>
                  <Button
                    variant="secondary"
                    onClick={() => onOverrideTask("regression")}
                    disabled={busy}
                  >
                    Treat as regression
                  </Button>
                </div>
              </div>
            ) : null}

            {profile.problem_type !== "regression" && profile.class_balance_ratio !== null ? (
              <div className="mt-6 border-t border-separator pt-5">
                <ClassBalanceChart
                  problemType={profile.problem_type}
                  classBalanceRatio={profile.class_balance_ratio}
                  targetColumn={targetColumn}
                />
              </div>
            ) : null}
          </Card>

          <Card>
            <CardHeader title="Data quality" />

            <p className="label-caps mb-3 text-text-tertiary">What was flagged</p>
            <QualityInsights profile={profile} />

            <div className="mt-6 border-t border-separator pt-5">
              <p className="label-caps mb-3 text-text-tertiary">System warnings</p>
              <SystemWarnings profile={profile} />
            </div>

            <p className="mt-4 font-mono text-data-sm leading-relaxed text-text-tertiary">
              A flag is a fact with a threshold behind it, not a decision - the strategy step
              chooses what to do about them.
            </p>
          </Card>
        </div>

        <div className="space-y-6">
          <MetricPanel
            problemType={profile.problem_type}
            primaryMetric={profile.primary_metric}
            secondaryMetrics={profile.secondary_metrics}
            classBalanceRatio={profile.class_balance_ratio}
          />

          <Card>
            <CardHeader title="Feature scope" />
            <p className="text-body-sm leading-relaxed text-text-secondary">
              Exclude a feature only when you do not want it available to the generated pipeline. Your computed profile remains unchanged.
            </p>
            <div className="mt-4 flex items-center justify-between gap-3 border-y border-separator py-3">
              <span className="font-mono text-data-sm text-text-secondary">
                {excludedColumns.length === 0 ? "All features included" : `${excludedColumns.length} excluded`}
              </span>
              <span className="font-mono text-data-sm text-text-tertiary">
                {featureColumns.length} available
              </span>
            </div>
            <details className="group mt-4">
              <summary className="cursor-pointer list-none font-mono text-data-sm text-accent-ink marker:hidden">
                <span className="group-open:hidden">Choose exclusions</span>
                <span className="hidden group-open:inline">Hide feature list</span>
              </summary>
              <fieldset className="mt-3 max-h-56 space-y-2 overflow-y-auto pr-1">
                <legend className="sr-only">Features to exclude from generated code</legend>
                {featureColumns.map((column) => {
                  const isExcluded = excludedColumns.includes(column.name);
                  return (
                    <label
                      key={column.name}
                      className="flex cursor-pointer items-center justify-between gap-3 rounded-sm border border-border px-3 py-2 text-data transition-colors hover:border-accent/40 hover:bg-accent-subtle"
                    >
                      <span className="min-w-0 truncate font-mono text-text-primary">{column.name}</span>
                      <span className="flex shrink-0 items-center gap-2 text-text-secondary">
                        <span>{isExcluded ? "Excluded" : "Included"}</span>
                        <input
                          type="checkbox"
                          checked={isExcluded}
                          onChange={() => toggleExclusion(column.name)}
                          disabled={busy}
                          aria-label={`Exclude ${column.name} from generated code`}
                        />
                      </span>
                    </label>
                  );
                })}
              </fieldset>
            </details>
          </Card>
        </div>
      </div>

      <Card padded={false} className="overflow-hidden">
        <div className="flex items-center justify-between gap-4 border-b border-border px-5 py-4">
          <h2 className="text-heading font-heading text-text-primary">Columns</h2>
          <span className="label-caps text-text-tertiary">{profile.n_columns} total</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="label-caps border-b border-border bg-sunken text-text-tertiary">
                <th className="px-5 py-2 font-bold">Column</th>
                <th className="px-3 py-2 font-bold">Type</th>
                <th className="px-3 py-2 font-bold">Missing</th>
                <th className="px-3 py-2 font-bold">Unique</th>
                <th className="px-3 py-2 font-bold">Sample values</th>
                <th className="px-5 py-2 font-bold">Flags</th>
              </tr>
            </thead>
            <tbody>
              {profile.columns.map((column) => {
                const isTarget = column.name === profile.target_column;
                return (
                  <tr
                    key={column.name}
                    className={`border-b border-separator last:border-0 ${
                      isTarget ? "bg-accent-subtle" : "hover:bg-sunken"
                    }`}
                  >
                    <td className="whitespace-nowrap px-5 py-2 font-mono text-data text-text-primary">
                      {column.name}
                      {isTarget ? (
                        <span className="ml-2 rounded-tag bg-accent px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-white">
                          target
                        </span>
                      ) : null}
                    </td>
                    <td className="px-3 py-2">
                      <DataTag>{column.inferred_type.replace(/_/g, " ")}</DataTag>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-1 w-12 shrink-0 overflow-hidden rounded-full bg-border"
                          aria-hidden
                        >
                          <span
                            className={`block h-full ${
                              column.missing_pct > 0.5 ? "bg-error" : "bg-text-tertiary"
                            }`}
                            style={{ width: `${Math.min(column.missing_pct, 1) * 100}%` }}
                          />
                        </span>
                        <span className="font-mono text-data-sm text-text-secondary">
                          {pct(column.missing_pct)}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-2 font-mono text-data-sm text-text-secondary">
                      {column.unique_count.toLocaleString()}
                    </td>
                    <td className="max-w-xs truncate px-3 py-2 font-mono text-data-sm text-text-tertiary">
                      {column.sample_values ? column.sample_values.join(", ") : "-"}
                    </td>
                    <td className="px-5 py-2">
                      <div className="flex flex-wrap gap-1">
                        {column.flags.length > 0
                          ? column.flags.map((flag) => <QualityChip key={flag} flag={flag} />)
                          : null}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          variant="secondary"
          onClick={onBack}
          icon={<ChevronLeftIcon className="size-4" />}
          disabled={busy}
        >
          Change target
        </Button>
        <Button onClick={onGenerate} loading={busy} iconRight={<ArrowRightIcon className="size-4" />}>
          {busy ? "Generating strategy" : "Generate strategy"}
        </Button>
      </div>
    </div>
  );
}
