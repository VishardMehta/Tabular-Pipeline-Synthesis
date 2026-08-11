/**
 * One selectable column name.
 *
 * Deliberately carries only a name. DatasetUploadResponse has nothing else
 * per column yet - no inferred type, no missingness, no unique count. That
 * data does not exist until /profile runs, which is why it appears on the
 * Profile screen instead. Section 44: "Do not overwhelm the user with every
 * statistic yet" - here that is not a choice, it is what the API allows.
 */

export function ColumnRow({
  name,
  selected,
  onSelect,
}: {
  name: string;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={`flex w-full items-center gap-3 rounded-sm px-4 py-3 text-left transition-colors duration-150 ${
        selected ? "bg-accent-subtle" : "hover:bg-surface-hover"
      }`}
    >
      <span
        className={`flex size-4 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
          selected ? "border-accent" : "border-border"
        }`}
      >
        {selected ? <span className="size-1.5 rounded-full bg-accent" /> : null}
      </span>
      <span
        className={`truncate font-mono text-secondary-size ${
          selected ? "font-medium text-text-primary" : "text-text-primary"
        }`}
      >
        {name}
      </span>
    </button>
  );
}
