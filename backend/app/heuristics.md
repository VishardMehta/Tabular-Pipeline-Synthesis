# heuristics.md

Companion to `heuristics.py`. The constants file holds one comment per value:
why that number, and what moving it costs in each direction. This file holds the
rules that span several constants at once and therefore belong to no single one.

Read this before writing the profiler. Every section below describes a way to
implement `heuristics.py` correctly and still get the wrong answer.

---

## Sampling changes what three of the flags mean

When `n_rows` exceeds `SAMPLE_THRESHOLD` the profiler computes on a sample and
sets `ProfileCard.profiled_on_sample`. Two consequences follow, and they are not
symmetric.

**Ratio-based flags compute against the sample row count, not the true row
count.** A proportion estimated from a random sample is unbiased, so
`missing_pct`, `top_value_pct` and every threshold read against them stay
correct. `HIGH_MISSING_P` and `QUASI_CONSTANT_P` are safe.

**`unique_count` is a sample estimate and it undercounts.** This is the part
that breaks. Distinct-value counts do not subsample: a column with 5,000
distinct values, sampled down to 200,000 rows from 2,000,000, will show
materially fewer than 5,000, and there is no correction factor that recovers the
true count without seeing the full column. The undercount is always downward,
never upward.

The three constants reading `unique_count` therefore behave differently under
sampling:

| Constant | Survives sampling | Why |
|---|---|---|
| `ID_UNIQUENESS` | Yes | A true identifier is near-unique in any sample of any size, because every row it does appear in still carries a distinct value. The ratio holds. |
| `HIGH_CARD_REL` | **No** | It reads `unique_count / n_rows`. Under sampling the numerator falls but the denominator falls to the sample size too, and the two do not fall at the same rate. An ordinary 200-category column in a 2,000,000-row file has a true ratio of 0.0001, and in a 200,000-row sample it is still 200 distinct over 200,000 rows. The failure is worse for genuinely high-cardinality columns, where the sampled ratio inflates toward 1.0 and the flag fires on columns that are not high cardinality relative to the real file. It over-flags. |
| `HIGH_CARD_ABS` | Partially | The absolute count can only fall, so this under-flags rather than over-flags. A column just above 50 distinct in the full file may sample to just below it. Safer direction, still wrong. |

**The rule: compute cardinality on the full column even when every other
statistic comes from the sample.** `nunique()` over one column of a large frame
is cheap. The sampling exists for the correlation matrix and the datetime parse
loops, which are the expensive parts, not for counting distinct values.

If that ever becomes too slow to do for every column, the fallback is to record
the undercount honestly rather than to flag on a bad number: leave
`unique_count` as the sample estimate, and suppress `HIGH_CARD_REL` entirely
when `profiled_on_sample` is true.

---

## Metric selection

`class_balance_ratio` is the class balance ratio. Its definition is
problem-type-dependent and that is deliberate, because the binary definition
does not transfer.

**Binary classification.** `class_balance_ratio = n_majority / n_minority`.
The bands apply directly:

| Condition | Primary |
|---|---|
| `class_balance_ratio <= BALANCE_ACCURACY_MAX` | `accuracy` |
| `BALANCE_ACCURACY_MAX < class_balance_ratio <= BALANCE_F1_MAX` | `f1` |
| `class_balance_ratio > BALANCE_F1_MAX` | `pr_auc` |

**Multiclass classification.** The primary is `f1_macro` regardless of ratio.
The bands are not read. A fifteen-class dataset that is entirely reasonable to
model can show a 12:1 spread between its largest and smallest class, which would
route it to `pr_auc` under the binary rule, and `pr_auc` is not well defined for
multiclass without an averaging choice that nobody asked for.

An alternative definition, `(1 / n_classes) / min_class_proportion`, was
proposed and rejected during stage 2. It was meant to generalise past binary
without leaning on "majority" and "minority" - but multiclass never reads this
value against the bands at all, so there was nothing left to generalise for.
The two formulas also disagree numerically at every imbalance away from an
even split (9.0 versus 5.0 at a 90/10 split), and `n_majority / n_minority` is
what `BALANCE_ACCURACY_MAX` and `BALANCE_F1_MAX` were calibrated against.

**Regression.** The primary is `rmse`, always. No bands, no branch. See the
comment on `TARGET_SKEW_THRESHOLD` for why the metric does not switch to `mae`
on skewed targets.

### Secondary metrics are never optional

Every problem type reports secondaries alongside the primary, populated by the
same function that picks the primary. A recommendation of F1 that suppresses
accuracy is precisely the black-box behaviour this tool positions against: shown
alone, a headline metric cannot be checked for whether it was chosen to flatter
the result.

| Problem type | Primary | Secondary |
|---|---|---|
| Binary | per bands | the two bands not selected, plus `roc_auc` |
| Multiclass | `f1_macro` | `accuracy` |
| Regression | `rmse` | `mae`, `r2` |

`roc_auc` is reachable only as a secondary on binary classification. That is not
an oversight. It is a useful diagnostic and a poor primary under imbalance,
because it is computed against the true negatives that imbalance makes abundant,
so it stays flattering while precision collapses. No band selects it and none
should.

`r2` is never primary. It is scale-free, so it hides the magnitude of the error,
which is usually the number the user actually needs.

---

## Flags are facts, decisions belong to the model

Every member of `ColumnFlag` maps to exactly one constant, and a flag never
drops a column. The profiler reports; `GenResult.dropped_columns` decides. Two
places where this matters concretely:

- `QUASI_CONSTANT` must never be applied to the target column. A target that is
  1% positive is the definition of an imbalanced classification problem, not a
  defect in the column.
- `HIGH_MISSING` on a missing-not-at-random column is a suggestion to drop
  something where a missing-indicator feature would be better. The flag cannot
  tell the difference, and it is not supposed to try.

---

## Thresholds that are strict rather than inclusive

`HIGH_CARD_ABS` compares with strict greater-than. US states are exactly 50 and
one-hot encoding 50 states is ordinary practice, not a warning. Any constant
whose value sits on a natural boundary needs its comparison direction stated,
not inferred.
