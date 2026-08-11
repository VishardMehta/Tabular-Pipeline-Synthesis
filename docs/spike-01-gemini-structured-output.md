# Spike 01: Gemini structured output against GenResult

Run at the end of stage 0, before stage 1, against `google-genai` 2.17.0.

Purpose: the frozen plan lists "Gemini rejects the nested GenResult schema" and
"field ordering is not preserved" as risks 1 and 2, to be tested on day one of
stage 3. They were pulled forward because both are defects in `models.py`, and
`models.py` had just been declared final. Getting the schemas wrong on day 1
costs nothing; on day 20 it costs everything built on top.

Method: inspect the schema the SDK actually transmits, then ten real generations
against the stage 0 fixture profile.

---

## Result summary

| Question | Answer |
|---|---|
| Nested models accepted | Yes. 9/9 calls that reached a model. |
| Field order preserved on the wire | Yes. 9/9. |
| `Metric` enum enforced as a schema constraint | Yes. |
| `max_length` / `max_items` transmitted | Yes. |
| Planted leakage column dropped | Yes. 9/9. |
| Referenced only names the code defines | Yes, once derived features are accounted for. |

Neither fallback in the plan is needed. `DroppedColumn`, `PreprocessingStep`
and `CandidateModel` stay as nested models rather than flattening to
`list[str]`, and the field sequence does not need restating in prompt text.

---

## The locked model is gone

`gemini-2.5-flash`, locked in section 0 of the plan, returns 404 for a newly
issued API key: "no longer available to new users". Ten out of ten calls.

It still appears in `client.models.list()` and still 404s on
`generateContent`. **The model listing is a catalogue, not an entitlement
check.** Do not build an availability probe on it.

Flash tier measured with the real `GenResult` schema, one call each:

| Model | Accepted | Latency | Code produced |
|---|---|---|---|
| `gemini-3.6-flash` | yes | 17.4s | 57 lines |
| `gemini-3.5-flash` | yes | 23.6s | 67 lines |
| `gemini-flash-latest` | yes | 23.1s | 53 lines |
| `gemini-3.1-flash-lite` | yes | 3.7s | **1 line** |

The plan's reasoning outlived its model name: Flash-Lite is still too weak for
pipeline code, returning a one-line pipeline.

Avoid `gemini-flash-latest` despite the convenience. A floating alias means
cassettes and prompt tuning drift underneath the project with no diff, which is
the same failure mode the pandas pin exists to prevent.

---

## Descriptions are prompt surface

The finding with the longest reach, because it changes what a docstring *is* in
`models.py`.

`google-genai` serialises the docstring of every class reachable from the
response schema into the request as a `description`. Engineering rationale
written for a colleague becomes instruction text for the model. Before this was
caught, `primary_metric` was being sent as:

> "Closed set of primary metrics. Closed rather than free text so the LLM cannot
> invent a metric that the validator has no rule for, and so the frontend can
> label it confidently."

There is a sharp edge underneath it. Pydantic emits `$ref` plus a sibling
`description` for enum-typed and single-nested-model fields. The SDK inlines the
`$ref` by replacing the entire node, which discards the sibling. Measured:

| Field shape | `Field(description=...)` |
|---|---|
| enum-typed (`problem_type`, `primary_metric`) | **silently discarded** |
| single nested model | **silently discarded** |
| `list[Model]` (`dropped_columns`, `preprocessing`, `candidate_models`) | survives |
| plain scalar | survives |

So the two enum fields on `GenResult` cannot be steered by a field description
at all. Their enum class docstrings are the only lever.

The resulting invariant now sits at the top of `models.py`: `#` comments are for
humans, docstrings and `Field(description=...)` are prompt surface. A strict
`xfail` test holds stage 3 to authoring the real descriptions.

---

## Column references: the validator's first real lesson

Two of nine runs named columns absent from the dataset. They are not
hallucinations. The code creates them first:

```python
df['signup_year']       = df['signup_date'].dt.year
df['signup_month']      = df['signup_date'].dt.month
df['signup_dayofweek']  = df['signup_date'].dt.dayofweek
df['signup_days_since'] = (max_date - df['signup_date']).dt.days
```

**A hallucinated-column check that compares referenced names against the profile
alone will report every engineered feature as a hallucination.** On this
evidence that is a false positive on roughly 20% of generations, which is enough
to train the user to ignore the check entirely - the same failure the "checklist
that always passes" note warns about from the other direction.

Stage 4 requirement: the check must first collect names the code *defines*
(`df['x'] = ...`, `assign(...)`, `rename(...)`, transformer outputs) and flag
only references that are in neither the profile nor that set. `SIMILARITY_CUTOFF`
near-miss suggestions apply only to what survives both.

---

## Reliability observations

Both from the same ten calls, both cheap to note now and expensive to discover
in stage 3.

**503 is a distinct failure from 429.** One call returned `503 UNAVAILABLE`,
"experiencing high demand". The plan specifies catching 429 as
`LLM_RATE_LIMITED` with `retryable: true`. 503 is transient, unrelated to quota,
and needs its own code and the same retry affordance. A 10% transient failure
rate makes this a routine path, not an edge case.

**One run in nine produced a one-line pipeline** on the capable model. Schema
validation passed, since a one-line string is a valid `str`. Structural
minimums, such as a floor on code length or a required `fit` call, cannot be
expressed in the response schema and must live in the validator.

---

## Reproducing

The spike script is not committed. It reads `GOOGLE_API_KEY`, prints the
transmitted schema, then runs `RUNS` generations reporting key order, column
references and whether the planted `churn_reason` leak was dropped.
