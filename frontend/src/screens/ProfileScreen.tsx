/** Screen 2: the computed facts. Every number here came from Python. */

import { Button } from "../components/shared/Button";
import { Card, SectionHeading } from "../components/shared/Card";
import { ClassBalanceChart } from "../components/profile/ClassBalanceChart";
import { MetricPanel } from "../components/profile/MetricPanel";
import { QualityChip } from "../components/profile/QualityChip";
import { StatTile } from "../components/profile/StatTile";
import { TaskConfidenceToggle } from "../components/profile/TaskConfidenceToggle";
import { WarningRow } from "../components/profile/WarningRow";
import type { ColumnFlag, ProfileCard } from "../types";

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

function countFlag(profile: ProfileCard, flag: ColumnFlag): number {
  return profile.columns.filter((column) => column.flags.includes(flag)).length;
}

function averageMissing(profile: ProfileCard): number {
  if (profile.columns.length === 0) return 0;
  const total = profile.columns.reduce((sum, column) => sum + column.missing_pct, 0);
  return total / profile.columns.length;
}

export function ProfileScreen({
  profile,
  onGenerate,
  onBack,
  busy,
}: {
  profile: ProfileCard;
  onGenerate: () => void;
  onBack: () => void;
  busy: boolean;
}) {
  const targetColumn = profile.columns.find((column) => column.name === profile.target_column);
  const leakageCount = countFlag(profile, "potential_leakage");
  const highMissingCount = countFlag(profile, "high_missing");
  const needsAttention = leakageCount > 0 || highMissingCount > 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-title font-title text-text-primary">Dataset profile</h2>
        <p className="mt-2 text-secondary-size text-text-secondary">
          {profile.n_rows.toLocaleString()} rows &middot; {profile.n_columns} columns &middot;{" "}
          {profile.profiled_on_sample
            ? `profiled on a ${profile.sample_rows?.toLocaleString()}-row sample`
            : "profiled on the full file"}
        </p>
      </div>

      <Card>
        <SectionHeading>Overview</SectionHeading>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          <StatTile label="Rows" value={profile.n_rows.toLocaleString()} />
          <StatTile label="Columns" value={String(profile.n_columns)} />
          <StatTile label="Duplicate rows" value={profile.duplicate_row_count.toLocaleString()} />
          <StatTile label="Avg. missing" value={pct(averageMissing(profile))} />
        </div>
      </Card>

      <Card>
        <SectionHeading>Data quality</SectionHeading>
        <StatusList
          rows={[
            {
              label: "Possible leakage",
              value: String(leakageCount),
              tone: leakageCount > 0 ? "error" : "success",
            },
            {
              label: "High-missing columns",
              value: String(highMissingCount),
              tone: highMissingCount > 0 ? "warning" : "success",
            },
            { label: "Constant columns", value: String(countFlag(profile, "constant")), tone: "neutral" },
            { label: "ID-like columns", value: String(countFlag(profile, "id_like")), tone: "neutral" },
            {
              label: "High-cardinality columns",
              value: String(countFlag(profile, "high_cardinality")),
              tone: "neutral",
            },
          ]}
        />
        <p className="mt-3 text-caption text-text-tertiary">
          {needsAttention
            ? "Flagged by dataset analysis - review before trusting the generated pipeline as-is."
            : "No leakage or high-missing columns detected."}
        </p>
      </Card>

      <Card>
        <SectionHeading>Target</SectionHeading>
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-heading font-heading text-text-primary">
            {profile.target_column}
          </span>
          <span className="text-secondary-size text-text-secondary">
            {profile.problem_type.replace(/_/g, " ")}
          </span>
          <TaskConfidenceToggle confidence={profile.task_confidence} />
        </div>
        <div className="mt-5">
          <ClassBalanceChart
            problemType={profile.problem_type}
            classBalanceRatio={profile.class_balance_ratio}
            targetColumn={targetColumn}
          />
        </div>
      </Card>

      <MetricPanel
        problemType={profile.problem_type}
        primaryMetric={profile.primary_metric}
        secondaryMetrics={profile.secondary_metrics}
        classBalanceRatio={profile.class_balance_ratio}
      />

      <Card className="p-0">
        <div className="p-6 pb-0">
          <SectionHeading>Columns</SectionHeading>
        </div>
        <div className="overflow-x-auto px-6 pb-6">
          <table className="w-full border-collapse text-left text-secondary-size">
            <thead>
              <tr className="border-b border-separator text-caption uppercase tracking-wide text-text-tertiary">
                <th className="py-2 pr-4 font-medium">Column</th>
                <th className="py-2 pr-4 font-medium">Type</th>
                <th className="py-2 pr-4 font-medium">Missing</th>
                <th className="py-2 pr-4 font-medium">Unique</th>
                <th className="py-2 pr-4 font-medium">Values</th>
                <th className="py-2 font-medium">Flags</th>
              </tr>
            </thead>
            <tbody>
              {profile.columns.map((column) => (
                <tr
                  key={column.name}
                  className={`border-b border-separator last:border-0 ${
                    column.name === profile.target_column ? "bg-accent-subtle/40" : ""
                  }`}
                >
                  <td className="py-2.5 pr-4 font-mono font-medium text-text-primary">
                    {column.name}
                    {column.name === profile.target_column ? (
                      <span className="ml-2 rounded-full bg-accent px-2 py-0.5 text-[10px] font-medium text-text-on-accent">
                        target
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2.5 pr-4 text-text-secondary">
                    {column.inferred_type.replace(/_/g, " ")}
                  </td>
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-2 text-text-secondary">
                      <div className="h-1.5 w-14 overflow-hidden rounded-full bg-surface-secondary">
                        <div
                          className={`h-full ${column.missing_pct > 0.5 ? "bg-warning" : "bg-text-tertiary"}`}
                          style={{ width: `${Math.min(column.missing_pct, 1) * 100}%` }}
                        />
                      </div>
                      {pct(column.missing_pct)}
                    </div>
                  </td>
                  <td className="py-2.5 pr-4 text-text-secondary">
                    {column.unique_count.toLocaleString()}
                  </td>
                  <td className="py-2.5 pr-4 text-text-tertiary">
                    {column.sample_values ? column.sample_values.join(", ") : "–"}
                  </td>
                  <td className="py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {column.flags.map((flag) => (
                        <QualityChip key={flag} flag={flag} />
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Change target
        </Button>
        <Button onClick={onGenerate} loading={busy}>
          {busy ? "Generating strategy" : "Generate strategy"}
        </Button>
      </div>
    </div>
  );
}

function StatusList({
  rows,
}: {
  rows: { label: string; value: string; tone: "success" | "warning" | "error" | "neutral" }[];
}) {
  return (
    <div>
      {rows.map((row) => (
        <WarningRow key={row.label} label={row.label} value={row.value} tone={row.tone} />
      ))}
    </div>
  );
}
