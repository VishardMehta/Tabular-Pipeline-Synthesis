# Agentic AutoML

## Core rule
Python computes facts. The LLM reasons over facts. The LLM never sees raw data.
llm.py accepts a ProfileCard, never a DataFrame. Do not change that signature.

## Hard constraints
- No LangChain, LangGraph, Instructor, ydata-profiling, Redis, Celery,
  SQLAlchemy, pyarrow. Do not add dependencies without asking.
- Gemini SDK is `google-genai`. NOT `google-generativeai` (deprecated).
- All thresholds live in heuristics.py as named constants. No magic numbers
  anywhere else.
- GenResult has no field that can hold a metric value. Never add one.
  MVP-1 does not execute code, so any displayed score would be fabricated.
- CSV reads use the pandas C engine everywhere, including in generated code.
- No em dashes in any output, comments, or docs. Use hyphens.
- `.env.example` contains variable names with empty values. Never a real
  value, not even temporarily. Real values go in `.env`, which is gitignored.

## models.py has two audiences
`#` comments are for humans: rationale, tradeoffs, why a number. Docstrings and
`Field(description=...)` are prompt surface, sent to the model as instruction
text whenever a class is used as a response_schema. Never put internal
reasoning in a docstring.

Field descriptions are discarded on enum-typed and single-nested-model fields,
because the SDK inlines the `$ref` and drops its siblings. Those fields are
steered by the enum or model docstring instead. See
docs/spike-01-gemini-structured-output.md.

## GenResult field order is load-bearing
Strategy fields must precede `code` so the model plans before it writes.
Do not reorder.

## Prompt authoring: say Y, never write "never X" alone
A bare prohibition in a system prompt is weaker than telling the model what to
say instead. Found in stage 3: instructing the model not to call
`target_association` a "linear" correlation stopped it on some datasets but not
others. Giving it the actual vocabulary to use ("call it an association";
naming what it is per column via `association_method`) fixed every case,
confirmed by rerunning the same fixture that still failed under the
prohibition-only version. Applies again in stage 4 when writing the
validator's failure messages: tell the model what a passing version looks
like, not only what a failing one does.

## Testing
Profiler and validator changes require a fixture. Never assert on exact LLM
prose; assert structural invariants only.

A known trap deferred to a later stage gets a `pytest.mark.xfail(strict=True)`
test now, with a reason naming the stage that must fix it. A documented trap
with no failing test is still a trap. Strict, so it also fails once the trap is
fixed and the marker is stale.
