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

## GenResult field order is load-bearing
Strategy fields must precede `code` so the model plans before it writes.
Do not reorder.

## Testing
Profiler and validator changes require a fixture. Never assert on exact LLM
prose; assert structural invariants only.
