/**
 * A label/value pair, not a card. Section 14: "Better: Dataset overview /
 * 18,432 rows  24 columns  2.4 MB" - grouped stats in one row read faster
 * than the same numbers each boxed on their own.
 */

export function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-caption font-caption uppercase tracking-wide text-text-tertiary">
        {label}
      </p>
      <p className="mt-1 text-heading font-heading text-text-primary">{value}</p>
    </div>
  );
}
