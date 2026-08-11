/** Screen 2: the computed facts. Every number here came from Python. */

import { Bar, Button, Card, FlagBadge, SectionTitle } from "../components/ui";
import type { ProfileCard } from "../types";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

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
  return (
    <div className="space-y-4">
      <Card>
        <SectionTitle>Dataset</SectionTitle>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <Stat label="Rows" value={profile.n_rows.toLocaleString()} />
          <Stat label="Columns" value={String(profile.n_columns)} />
          <Stat label="Target" value={profile.target_column} />
          <Stat label="Task" value={profile.problem_type.replace(/_/g, " ")} />
          <Stat label="Metric" value={profile.primary_metric} />
        </div>
        {/* The alternatives are shown, not suppressed. A primary metric on its
            own cannot be checked for whether it was picked to flatter. */}
        {profile.secondary_metrics.length > 0 ? (
          <p className="mt-3 text-sm text-slate-600">
            Also reported: {profile.secondary_metrics.join(", ")}
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
          <span>Task confidence {pct(profile.task_confidence)}</span>
          {profile.class_balance_ratio !== null ? (
            <span>Class balance {profile.class_balance_ratio.toFixed(2)}:1</span>
          ) : null}
          <span>Duplicate rows {profile.duplicate_row_count}</span>
          {/* Reported honestly rather than hidden. A sampled profile is a different claim. */}
          <span>
            {profile.profiled_on_sample
              ? `Profiled on a ${profile.sample_rows?.toLocaleString()} row sample`
              : "Profiled on the full file"}
          </span>
        </div>
      </Card>

      <Card>
        <SectionTitle>Columns</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
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
                  className={`border-b border-slate-100 ${
                    column.name === profile.target_column ? "bg-slate-50" : ""
                  }`}
                >
                  <td className="py-2 pr-4 font-medium text-slate-900">
                    {column.name}
                    {column.name === profile.target_column ? (
                      <span className="ml-2 rounded bg-slate-900 px-1.5 py-0.5 text-[11px] text-white">
                        target
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2 pr-4 text-slate-600">
                    {column.inferred_type.replace(/_/g, " ")}
                  </td>
                  <td className="py-2 pr-4">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Bar value={column.missing_pct} tone={column.missing_pct > 0.5 ? "amber" : "slate"} />
                      {pct(column.missing_pct)}
                    </div>
                  </td>
                  <td className="py-2 pr-4 text-slate-600">
                    {column.unique_count.toLocaleString()}
                  </td>
                  <td className="py-2 pr-4 text-slate-500">
                    {/* Only low-cardinality categoricals carry level names. */}
                    {column.sample_values ? column.sample_values.join(", ") : "-"}
                  </td>
                  <td className="py-2">
                    <div className="flex flex-wrap gap-1">
                      {column.flags.map((flag) => (
                        <FlagBadge key={flag} flag={flag} />
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
        <Button onClick={onGenerate} disabled={busy}>
          {busy ? "Generating..." : "Generate pipeline"}
        </Button>
      </div>
    </div>
  );
}
