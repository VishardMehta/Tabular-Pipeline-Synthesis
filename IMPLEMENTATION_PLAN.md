# Agentic AutoML MVP-1: Implementation Plan

Solo developer. Gemini free tier. MVP-1.5 local execution included, gated off by default.
Architecture is frozen per the final blueprint. This document is the build order.

---

## 0. Decisions locked before you write a line

These were left vague in the blueprint. Deciding them now prevents rework.

| Question | Decision | Reason |
|---|---|---|
| Python version | 3.12 | Stable, all deps support it |
| Frontend language | TypeScript | Schemas mirror Pydantic; type drift is the main integration bug |
| CSV read engine | **C engine only. Drop pyarrow entirely.** | pyarrow has different null and dtype semantics, and no `chunksize`. If the profiler reads with pyarrow and the generated `pd.read_csv` uses the C engine, they disagree about the data. At 50MB the speed gain is irrelevant. Consistency wins. |
| Duplicate column names | **Reject the upload.** Error `DUPLICATE_COLUMNS`, message naming the offenders. | pandas mangles to `col`, `col.1`. The LLM then writes code referencing `col.1`, which does not exist in the user's file. Surfacing the mangling is possible but complicates every downstream layer for a rare case. |
| Gemini model | `gemini-2.5-flash` | Flash-Lite is too weak for pipeline code. Pro's free daily cap is trial-only. |
| Gemini SDK | `google-genai` | The unified SDK. `google-generativeai` is the deprecated one; do not let Claude Code reach for it from stale training data. |
| Prompt caching | None | Gemini's context caching has a high minimum token floor. Your prompt is ~2k tokens. Not applicable. |
| Frontend state | Single `useReducer` in `App.tsx` | Four screens, one flow. Redux and Zustand are both overkill, but screen-local state loses the profile on a failed generation. |

---

## 1. Dependency list

`backend/pyproject.toml`:

```
fastapi>=0.115
uvicorn[standard]>=0.32
pydantic>=2.9
pydantic-settings>=2.6
python-multipart>=0.0.12
pandas>=2.2
numpy>=2.1
google-genai>=1.0
# dev
pytest>=8.3
pytest-asyncio>=0.24
httpx>=0.27
ruff>=0.7
```

Not installing: scikit-learn, xgboost, pyarrow, langchain, instructor, ydata-profiling, redis, celery, sqlalchemy.

Note on scikit-learn: MVP-1 does not need it, but **MVP-1.5 does**, because the subprocess has to import it. Install it into a separate venv at `.venv-runner/`, not into the API's environment. Keeping them apart is what makes the phase-2 Docker boundary obvious later.

`frontend/`: react 18, vite, typescript, tailwindcss, recharts, react-dropzone, shiki.

---

## 2. Environment variables

`backend/.env.example`:

```
GOOGLE_API_KEY=
LLM_MODEL=gemini-2.5-flash
LLM_TIMEOUT_S=60

DEPLOYMENT_ENV=local          # local | hosted
ENABLE_LOCAL_EXECUTION=false  # refuses to start if true and DEPLOYMENT_ENV != local
EXECUTION_TIMEOUT_S=60
EXECUTION_SAMPLE_ROWS=500
RUNNER_PYTHON=.venv-runner/bin/python

UPLOAD_DIR=./data/uploads
DB_PATH=./data/app.db
DATASET_TTL_HOURS=24
MAX_FILE_MB=50
MAX_COLS=1000

CORS_ORIGINS=http://localhost:5173
```

The startup guard is not a convention, it is an assertion in `config.py` that raises on boot:

```python
if settings.enable_local_execution and settings.deployment_env != "local":
    raise RuntimeError(
        "ENABLE_LOCAL_EXECUTION is only permitted when DEPLOYMENT_ENV=local"
    )
```

---

## 3. Build order

The ordering principle for solo work: **get a walking skeleton end to end first, then deepen each layer.** At no point should you have three half-built layers and nothing to look at. Every stage below ends with something you can demo.

### Stage 0: Walking skeleton (6-8h)

Goal: click upload in the browser, see a hardcoded profile and a hardcoded code block. No real logic anywhere.

- Repo scaffold, both halves, ruff, pytest, git
- `models.py`: **all** Pydantic schemas, complete and final. ProfileCard, ColumnProfile, ColumnFlag, GenResult, its four nested models, ValidationReport, ValidationCheck, error envelope.
- `types.ts`: hand-mirror those schemas
- Three routes returning hardcoded fixtures matching the schemas exactly
- Four React screens rendering those fixtures
- CORS working

Definition of done: the full click-through works with fake data.

Why first: the schemas are the contract between every later stage. Getting them wrong on day 20 is expensive. Getting them wrong on day 1 costs nothing.

### Stage 1: Ingest (6h)

- Streaming size check (reject during upload, not after buffering)
- UUID storage path, original filename to DB only
- Parse with C engine, catch and map parse errors
- Duplicate column detection, reject
- Empty file, header-only, single-column, column-count checks
- SQLite `datasets` table, WAL mode on
- TTL cleanup on startup and hourly
- `errors.py` with the full error code enum

Definition of done: upload returns a real column list. Every rejection path returns a specific code and a message a human can act on.

### Stage 2: Profiler (14-16h)

The largest single piece. Build in this order:

1. `heuristics.py` first, constants only, nothing else in it
2. dtype classification, the seven-rule ladder, first match wins
3. Column flags
4. Task inference with `task_confidence`
5. `metrics.py`, the `r_bal` rule
6. Leakage check on a sample
7. Sampling above `SAMPLE_THRESHOLD`, `profiled_on_sample` set honestly
8. Assemble ProfileCard

**Write the fixture CSVs before the profiler, not after.** Fifteen tiny files in `tests/fixtures/`. Then write the profiler against them. This is the difference between a profiler that works on Titanic and one that works on the client's file, and it is the reason this stage is 16 hours and not 6.

Definition of done: every fixture profiles without raising, and the flags are correct on each. Screen 2 shows real numbers.

### Stage 3: LLM (10-12h)

- `prompts.py`: system prompt, code constraints, one worked example
- `llm.py`: `LLMProvider` protocol, `GeminiProvider`
- Structured output via `response_schema`
- Explicit handling for 429, timeout, malformed output
- `generations` table, store tokens and latency
- Record cassettes as you go

Gemini specifics that will bite you:

```python
from google import genai
client = genai.Client(api_key=settings.google_api_key)
resp = client.models.generate_content(
    model=settings.llm_model,
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": GenResult,
    },
)
result = GenResult.model_validate_json(resp.text)
```

Three risks, each with a fallback:

1. **Nested models.** `GenResult` contains `DroppedColumn`, `PreprocessingStep`, `CandidateModel`. Gemini's schema support is a subset of OpenAPI and has historically struggled with `$defs` and deep nesting. Test this on day one of stage 3. If it fails, flatten those three to lists of strings. Do not discover this in week five.
2. **Field ordering.** The plan-then-code effect depends on strategy fields being generated before `code`. Gemini's schema has a `propertyOrdering` concept, and the SDK should derive it from Pydantic declaration order. **Verify empirically**: generate ten times, check the raw JSON key order. If ordering is not preserved, state the sequence explicitly in the prompt text as a fallback.
3. **Rate limits.** One call per generation, so RPM is not your problem. RPD is, during prompt iteration. Use cassettes from the moment the first real response comes back. Catch 429 specifically and return `LLM_RATE_LIMITED` with `retryable: true`.

Definition of done: real generated pipeline appears in Screen 4. Cassettes exist. Rate limit produces a retry button, not a 500.

### Stage 4: Validation (7h)

- `compile()` check
- AST import allowlist
- Dangerous call denylist
- Hallucinated column detection
- GenResult self-consistency against ProfileCard
- Structural warnings
- Validation fixture corpus: nine bad code strings, each triggering exactly one check

On the similarity function: `difflib.SequenceMatcher(None, a, b).ratio() >= 0.85` for near-miss detection. `get_close_matches` is convenient but its default cutoff is 0.6, which is far too loose and will flag unrelated strings. Tune the 0.85 against real generations, not against intuition.

Definition of done: checklist renders on Screen 4. Every fixture triggers its intended check and nothing else.

### Stage 5: Frontend (20-24h)

Now that the data is real, build the actual UI. Screens 1, 1.5, 2, 3, 4 per the frozen spec. Loading states, error states, retry, sample datasets, copy and download, the persistent "not executed" label.

Definition of done: works on a stranger's CSV without you explaining anything.

### Stage 6: MVP-1.5 execution (6h)

- `sandbox.py`: `LocalSubprocessSandbox` implementing the `Sandbox` protocol
- Write a 500-row sample to a temp dir alongside the code as `data.csv`
- `subprocess.run([RUNNER_PYTHON, script], cwd=tmpdir, timeout=EXECUTION_TIMEOUT_S, capture_output=True)`
- Kill the process group on timeout, not just the parent
- Return `RunResult`, store it, render stdout and exit status in Screen 4
- Gated by `ENABLE_LOCAL_EXECUTION`, hard boot guard as above

Definition of done: with the flag on, Screen 4 shows "Executed on a 500-row sample" plus real stdout. With it off, nothing changes from stage 5.

### Stage 7: Hardening and docs (10h)

- API tests with a stubbed provider
- The two ADRs
- README with local setup including the runner venv
- Prompt injection line in the system prompt
- One run against three genuinely messy real-world CSVs you have not seen before

---

## 4. Effort summary

| Stage | Hours |
|---|---|
| 0 Walking skeleton | 7 |
| 1 Ingest | 6 |
| 2 Profiler | 15 |
| 3 LLM | 11 |
| 4 Validation | 7 |
| 5 Frontend | 22 |
| 6 Execution | 6 |
| 7 Hardening and docs | 10 |
| Integration and debugging | 15 |
| **Subtotal** | **99** |
| Contingency 20% | 20 |
| **Total** | **~120 hours** |

Solo, that is roughly 6 weeks at 20h/week, or 4 weeks at 30h/week. Claude Code compresses stages 0, 1 and 5 meaningfully and stages 2 and 4 barely, because those are decision work rather than typing. Call it **95-105 hours realistic with AI assistance.**

If someone is holding you to one week, the honest cut is: stages 0 through 4 plus a bare-bones frontend, no execution, no polish. That is roughly 50 hours and it is a prototype, not a deliverable.

---

## 5. Using Claude Code on this

Put this in `CLAUDE.md` at the repo root:

```markdown
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
```

How to drive it, in order of importance:

1. **Write `models.py` yourself.** Everything else derives from it. Hand-write it, or review it line by line if you generate it.
2. **One stage per session.** Do not ask it to build the profiler and the frontend in one go. Context degrades and you lose the ability to review.
3. **Fixtures before implementation, always.** Ask for the fixture CSVs and their expected profiles first, then the profiler. Otherwise it writes tests that pass against its own bugs.
4. **Never accept a heuristic without asking why that number.** This is where AI-generated code looks right and is silently wrong. Every constant in `heuristics.py` should be one you can defend.
5. **Watch for stale training data**: the deprecated Gemini SDK, `pandas.append`, sklearn API changes, Pydantic v1 syntax.

---

## 6. Ten things that will actually go wrong

1. Gemini rejects the nested `GenResult` schema. Test in the first hour of stage 3.
2. Field ordering is not preserved, so the plan-then-code effect silently disappears. Verify with raw JSON.
3. The profiler raises on a real CSV. This is why the fixtures come first.
4. Generated code references `col.1` from mangled duplicate names. Solved by rejecting at ingest, but only if you actually implement the check.
5. Frontend loses the profile when generation fails. Solved by `useReducer` at the top level.
6. `datetime` parsing on a full messy column hangs. Always parse on a 1,000-row sample with `errors="coerce"`.
7. RPD exhausted mid-iteration during prompt tuning. Cassettes from the first real response.
8. Subprocess timeout leaves an orphan. Kill the process group, and reap in a `finally`.
9. TypeScript types drift from Pydantic. Consider generating them from the OpenAPI schema once stage 0 stabilises.
10. Scope creep back toward the SRS. The "not building" list exists for this. Re-read it weekly.

---

## 7. First session

Do exactly this, nothing more:

1. `git init`, both halves, ruff and pytest configured, `CLAUDE.md` in place
2. Write `models.py` completely: every schema, every enum, final
3. Write `heuristics.py`: constants only, with a comment on each explaining the choice
4. Three FastAPI routes returning hardcoded fixtures that validate against those schemas
5. React app that clicks through all four screens on fake data

Stop there. The walking skeleton being real is what makes every subsequent stage a fill-in rather than an integration.
