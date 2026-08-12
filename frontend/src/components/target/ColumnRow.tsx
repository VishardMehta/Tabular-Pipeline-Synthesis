/**
 * One selectable column, as a table row.
 *
 * Deliberately carries only a name and its position. DatasetUploadResponse
 * has nothing else per column - no inferred type, no missingness, no unique
 * count - and that data does not exist until /profile runs, which is why the
 * mock's "Inferred Type / Unique Values / Missing Data" columns are absent
 * here and present on the Profile screen instead. The index is real: it is
 * the column's ordinal position in the CSV header, which is genuinely useful
 * when two columns have similar names.
 */

export function ColumnRow({
  name,
  index,
  selected,
  onSelect,
}: {
  name: string;
  index: number;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={`flex w-full items-center gap-4 border-b border-separator px-5 py-2.5 text-left transition-colors duration-150 last:border-b-0 ${
        selected ? "bg-accent-subtle" : "hover:bg-surface-secondary"
      }`}
    >
      <span
        aria-hidden
        className={`flex size-4 shrink-0 items-center justify-center rounded-full border transition-colors ${
          selected ? "border-accent bg-accent" : "border-border-strong bg-surface"
        }`}
      >
        {selected ? <span className="size-1.5 rounded-full bg-white" /> : null}
      </span>

      <span
        className={`min-w-0 flex-1 truncate font-mono text-data ${
          selected ? "font-semibold text-accent-ink" : "text-text-primary"
        }`}
      >
        {name}
      </span>

      <span className="shrink-0 font-mono text-data-sm text-text-tertiary">
        col {index + 1}
      </span>
    </button>
  );
}
