# The not-building list

`IMPLEMENTATION_PLAN.md` closes with:

> 10. Scope creep back toward the SRS. **The "not building" list exists for
>     this.** Re-read it weekly.

That list lived in the blueprint and was never committed, so for most of this
project there was nothing to test a feature request against. This is it.

**How to use it.** A proposal that appears here is closed. Reopening one is
fine, but it means editing this file with a reason, not quietly building it.
Each entry says what it is, why it is out, and what would have to change for it
to come back in.

---

## 1. Executing the generated code

**Out for MVP-1.** Stage 6 (`ENABLE_LOCAL_EXECUTION`) is designed but unbuilt:
separate `.venv-runner`, subprocess, killed by process group on timeout.

The rule that follows from this is the one most likely to be broken by
accident: **no number anywhere in this product may describe how well a
pipeline performs.** No accuracy, no F1, no "expected" score, no leaderboard,
no "best model" badge. `GenResult` has no field that can hold one and must
never gain one.

*Comes back when:* stage 6 lands, with the runner venv and the sandbox
boundary, and even then the number is labelled as measured on a 500-row sample.

## 2. Multi-target prediction

**Out.** One target column, chosen by the user, per profile.

Multi-output regression and multi-label classification would make
`problem_type`, `primary_metric`, `task_confidence` and `class_balance_ratio`
per-target, and turn `target_association` from a scalar per column into a
matrix. That changes `ProfileCard`, therefore the prompt, therefore all three
cassettes. The cost lands on the two most fragile files in the repo for a need
that is genuinely niche against "give me a defensible starting pipeline".

*Comes back when:* someone has three real datasets that need it, not one
hypothetical.

## 3. Unsupervised learning

**Out.** No clustering, no dimensionality reduction, no anomaly detection.

The entire profiler is built around a target column: task inference, metric
selection, class balance, leakage. Unsupervised has none of those, so it is not
a mode of this pipeline - it is a second pipeline.

## 4. User-chosen algorithms or hyperparameters

**Out.** The model choosing an approach *and justifying it against the
profile* is the product. A dropdown of estimators plus a hyperparameter grid
makes this a form with an LLM bolted on.

Note what is deliberately *in*: excluding columns (`excluded_columns`) and
asserting an ambiguous task (`problem_type_override`). Both are instructions
about the caller's own knowledge of their data, not substitutes for the
model's reasoning.

## 5. User-chosen preprocessing steps

**Out**, same reasoning. `PreprocessingStep.step` is free text rather than an
enum, so there is no fixed vocabulary to expose as a UI control even if we
wanted to.

## 6. Accepting a client-supplied `ProfileCard`

**Permanently out. This one is a security boundary, not a scope decision.**

`GenerateRequest` carries no profile data. A caller who can edit the profile
can make the model justify any pipeline at all, and the validator's
self-consistency check would still pass, because it compares the result
against the same forged profile.

The test for whether a new field is allowed: **is it a fact, or an
instruction?** Facts about the dataset are computed by Python, never accepted
from the caller. Instructions about what the caller wants are fine.

## 7. Editing the generated code in the browser

**Out.** An editable code box means the validation report on screen describes
code that is no longer there. Copy and download, then edit in a real editor.

## 8. Chat, follow-up turns, conversational refinement

**Out.** One profile in, one strategy out. A chat interface invites the user to
argue the model into a different answer with no new facts, which is exactly the
failure mode the "LLM reasons over facts" rule exists to prevent. It would also
multiply quota use per dataset against a 20/day free tier.

## 9. Accounts, projects, history, sharing

**Out.** Datasets are anonymous, keyed by UUID, deleted after
`DATASET_TTL_HOURS`. There is no user model anywhere in the schema.

## 10. Auth and rate limiting

**Out for local use, and a hard blocker for anything else.**

`DEPLOYMENT_ENV=hosted` exists as a concept with no protection behind it. Any
caller can consume the whole daily quota.

*Comes back when:* this is deployed anywhere other than localhost. It is not
optional at that point - it is the first thing built.

## 11. Dataset formats other than CSV

**Out.** No Excel, no Parquet, no JSON, no database connections. pyarrow was
dropped deliberately (locked decision, section 0 of the plan): if the profiler
reads with different semantics than the generated `pd.read_csv`, they disagree
about the same file.

## 12. Streaming or chunked profiling

**Out.** Files are capped at `MAX_FILE_MB` and read whole. Above
`SAMPLE_THRESHOLD` rows the leakage test samples; everything else is computed
on the full column.

## 13. Model or provider choice exposed to the user

**Out.** `LLM_MODEL` is deployment configuration, not a user setting. A
floating alias like `gemini-flash-latest` is separately forbidden: it would
drift cassettes and prompt tuning underneath the project with no diff, the same
failure the pandas pin exists to prevent.

## 14. Prompt customisation by the user

**Out**, and it is close to item 6. The system prompt is the product's
reasoning. Exposing it invites prompt injection and makes every generation
unreproducible.

---

## Adjacent rules that are not scope decisions

These are not "not building" items - they are constraints on how anything gets
built. Listed here because they get mistaken for scope questions.

- **No new dependencies without asking.** Explicitly barred: LangChain,
  LangGraph, Instructor, ydata-profiling, Redis, Celery, SQLAlchemy, pyarrow.
- **`google-genai`, never `google-generativeai`** - the latter is deprecated
  and models will reach for it from stale training data.
- **All thresholds live in `heuristics.py`** as named constants with a written
  defence. No magic numbers anywhere else.
- **CSV reads use the pandas C engine everywhere**, including inside generated
  code.
- **No em dashes** in any output, comment or doc.
- **`GenResult` field order is load-bearing** - strategy fields precede `code`
  so the model plans before it writes.
