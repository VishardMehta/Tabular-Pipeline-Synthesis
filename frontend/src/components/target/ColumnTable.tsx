/**
 * The column picker. Search is contextual and labelled for what it searches,
 * not a bare "Search...", and only appears when the list is worth filtering -
 * a 4-column file does not need a search box.
 *
 * Rows are a single dense column rather than a 3-up grid: DESIGN.md puts data
 * tables at the centre of this tool and asks for tight vertical rhythm, and a
 * one-per-line list of mono names is far easier to scan for a specific column
 * than a reflowed grid where alphabetical order runs across before it runs
 * down.
 */

import { useMemo, useState } from "react";
import { SearchIcon } from "../shared/icons";
import { ColumnRow } from "./ColumnRow";

const SEARCH_THRESHOLD = 12;

export function ColumnTable({
  columns,
  selected,
  onSelect,
}: {
  columns: string[];
  selected: string | null;
  onSelect: (column: string) => void;
}) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return columns.map((name, index) => ({ name, index }));
    const needle = query.trim().toLowerCase();
    return columns
      .map((name, index) => ({ name, index }))
      .filter((entry) => entry.name.toLowerCase().includes(needle));
  }, [columns, query]);

  return (
    <div>
      {columns.length > SEARCH_THRESHOLD ? (
        <div className="border-b border-border p-3">
          <div className="relative">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-tertiary" />
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search columns"
              aria-label="Search columns"
              className="w-full rounded-sm border border-border bg-surface py-2 pl-9 pr-24 font-mono text-data text-text-primary transition-colors placeholder:font-sans placeholder:text-text-tertiary focus:border-accent focus:outline-none"
            />
            <span
              className="label-caps pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary"
              aria-live="polite"
            >
              {filtered.length}/{columns.length}
            </span>
          </div>
        </div>
      ) : null}

      <div className="label-caps flex items-center gap-4 border-b border-border bg-sunken px-5 py-2 text-text-tertiary">
        <span className="size-4 shrink-0" aria-hidden />
        <span className="flex-1">Column name</span>
        <span className="shrink-0">Position</span>
      </div>

      <div
        role="radiogroup"
        aria-label="Target column"
        className="max-h-[26rem] overflow-y-auto"
      >
        {filtered.length > 0 ? (
          filtered.map((entry) => (
            <ColumnRow
              key={entry.name}
              name={entry.name}
              index={entry.index}
              selected={selected === entry.name}
              onSelect={() => onSelect(entry.name)}
            />
          ))
        ) : (
          <p className="px-5 py-10 text-center text-secondary-size text-text-tertiary">
            No columns match &ldquo;{query}&rdquo;. Clear the search to see all {columns.length}.
          </p>
        )}
      </div>
    </div>
  );
}
