/**
 * The column picker. Section 12: search should be contextual and labelled
 * for what it searches, not a bare "Search...". Only rendered when the list
 * is worth filtering - a 4-column file does not need a search box.
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
    if (!query.trim()) return columns;
    const needle = query.trim().toLowerCase();
    return columns.filter((name) => name.toLowerCase().includes(needle));
  }, [columns, query]);

  return (
    <div>
      {columns.length > SEARCH_THRESHOLD ? (
        <div className="relative mb-3">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-tertiary" />
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search columns"
            aria-label="Search columns"
            className="w-full rounded-sm border border-border bg-surface py-2 pl-9 pr-3 text-secondary-size text-text-primary placeholder:text-text-tertiary"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-caption text-text-tertiary">
            {filtered.length} of {columns.length}
          </span>
        </div>
      ) : null}

      <div
        role="radiogroup"
        aria-label="Target column"
        className="grid max-h-96 grid-cols-1 gap-0.5 overflow-y-auto rounded-md border border-separator p-1 sm:grid-cols-2 lg:grid-cols-3"
      >
        {filtered.length > 0 ? (
          filtered.map((name) => (
            <ColumnRow key={name} name={name} selected={selected === name} onSelect={() => onSelect(name)} />
          ))
        ) : (
          <p className="col-span-full py-6 text-center text-secondary-size text-text-tertiary">
            No columns match &ldquo;{query}&rdquo;.
          </p>
        )}
      </div>
    </div>
  );
}
