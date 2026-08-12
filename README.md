# AutoNexus

Upload a CSV, get back a machine-learning pipeline written for it, plus an
honest account of why, and what was checked.

## What is AutoNexus?

**Upload a spreadsheet, get back a machine-learning pipeline written for it -
plus an honest account of why, and what we checked.**

You upload a tabular CSV, pick the column you want to predict, and the app
walks it through five stages:

```
Upload  ->  Pick target  ->  Profile  ->  Strategy  ->  Pipeline
 CSV        the column       Python       the plan      the code
            to predict       measures     + reasons     + checks
```

The first two stages after upload - **Profile** and the metric selection
behind it - are pure deterministic Python: pandas and hand-written rules, no
model call. Only at **Strategy** does an LLM (Google Gemini) get involved, and
what it receives is never the dataset itself - it is a JSON summary of
statistics Python already computed: column types, missingness, cardinality,
class balance, and a leakage association score per column. The LLM reasons
over those facts and returns a structured strategy (what to drop, how to
preprocess, which models to try, how to validate) followed by the Python code
that implements exactly that strategy. Before you see it, that code is
statically checked - never executed - against a dozen rules: does it parse,
does it import only approved libraries, does it reference real columns, does
it match the strategy it just described.

**The generated code is never run in this version of the app, and no score is
ever shown for it.** That is a deliberate design decision, not a missing
feature - see [Why AutoNexus?](#why-autonexus) below.

## Why AutoNexus?

Most "AutoML" tools train a model behind the scenes and hand you a number:
"94% accurate." That number is only trustworthy if you trust everything that
happened upstream of it, invisibly. This project takes the opposite bet:

- **Facts are computed, never guessed.** Every statistic on the Profile screen
  came from pandas running on your actual file, not from the LLM estimating
  anything.
- **Raw rows never leave the server.** The LLM sees a JSON profile - dtypes,
  percentages, counts, a handful of category level names - never your data.
  See [LLM Architecture](#llm-architecture) for exactly what crosses that
  boundary and why.
- **Generated code is auditable, not a black box.** It is ordinary
  scikit-learn code you can read top to bottom before running it yourself,
  and it comes with the checklist that was run against it.
- **The reasoning is visible.** The strategy - which columns get dropped and
  why, which models are worth trying, how the result should be validated - is
  shown as a plan before you see a single line of code, and the code's field
  order is arranged so the model has to commit to that plan before writing.
- **Validation happens before you see the result, not instead of showing it.**
  A failing check does not hide the code; it is shown alongside it, so you
  decide what to do about it.

We never run the generated code in this version, and we never show a model
score anywhere in the product. `GenResult`, the data structure that carries
the AI's answer, has no field capable of holding a score, by design - see
[Known Limitations](#known-limitations).

## Current Status

This repository has no standalone SRS or design PDF committed to it. The
closest artifacts to a requirements document are
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) (the frozen architecture
and an eight-stage build order) and [`docs/not-building.md`](docs/not-building.md)
(an explicit list of what is deliberately out of scope, with reasons). The
status below is measured against those two documents plus the code itself,
not against an external file that does not exist in this repo.

### Implemented

- CSV upload with streaming size limits and structural validation (empty,
  header-only, single-column, too-many-columns, duplicate column names)
- Target column selection, with a coherence-checked override for the one
  genuinely ambiguous case (a discrete numeric target read as either
  classification or regression)
- Per-column feature exclusion (keep a column out of the generated pipeline
  entirely, independent of what the model would have chosen)
- Full deterministic profiling: dtypes, missingness, cardinality, duplicate
  rows, class balance, per-column target-association / leakage score
- Deterministic metric selection (accuracy / F1 / PR-AUC by balance band for
  binary classification; F1-macro for multiclass; RMSE for regression)
- LLM strategy and pipeline generation via Gemini structured output, with API
  key rotation across a 429 and one automatic repair attempt on malformed
  output
- Twelve static validation checks against the generated code (see
  [Validation](#validation))
- The full five-screen frontend workflow, with real per-screen URLs, back/
  forward navigation, and session recovery on refresh
- A read endpoint so a browser refresh does not discard a paid-for
  generation, and a usage endpoint reporting real token/latency counts per
  dataset
- SQLite persistence with WAL mode and an hourly TTL sweep (24h default)
- 212 backend tests (pytest), ruff-clean

### Partially implemented

- **Error repair.** `llm.py` retries once, automatically, but only when the
  model's JSON fails schema validation. A response that parses cleanly but
  fails a *validation check* (a hallucinated column, a forbidden import) is
  not retried - `ErrorCode.VALIDATION_FAILED` exists for exactly this and is
  never raised; the failing checklist ships alongside the code instead. A
  real repair-on-failed-check loop is unbuilt.
- **Large-dataset sampling.** Profiling switches to a random sample above
  `SAMPLE_THRESHOLD` (200,000 rows) for the one O(n×m) leakage-correlation
  step, and sets `profiled_on_sample` honestly when it does. There is no test
  fixture anywhere near that size, so the sampled code path is exercised by
  construction, not by a real test.

### Not implemented

- **Code execution of any kind.** No sandbox, no `LocalSubprocessSandbox`, no
  Docker runner. `ENABLE_LOCAL_EXECUTION` and its three sibling settings exist
  in `config.py` and gate nothing but a boot-time assertion; there is no
  `execution.py`, and scikit-learn is not installed in the backend
  environment at all.
- **Model training, scores, comparison, or feature importance.** Direct
  consequence of no execution. `GenResult` has no field that could hold a
  number like this.
- **Async jobs / progress polling.** `JobState` was deliberately narrowed to
  `pending | complete` after a prior six-state version was found to never
  transition through its other four members. `/profile` and `/generate` are
  synchronous HTTP calls; there is no jobs table and no `GET /jobs/{id}`.
- **Distribution / histogram chart data.** The profiler computes a full
  `value_counts()` per column internally and keeps only the top five values
  plus a percentage - no bins, quantiles, or per-level counts are exposed
  anywhere in the API.
- **User-chosen algorithms, hyperparameters, or preprocessing steps.**
  Deliberate - see [`docs/not-building.md`](docs/not-building.md) item 4-5.
- **Metric override.** The task type is overridable; the evaluation metric is
  always re-derived from the (possibly overridden) task, never chosen by the
  caller.
- **Multi-target prediction, unsupervised learning.** One target column, one
  supervised pipeline. See [`docs/not-building.md`](docs/not-building.md)
  items 2-3.
- **File formats other than CSV.** No Excel, Parquet, JSON, or database
  connections.
- **Authentication, accounts, or multi-user rate limiting.** There is an
  in-process guard against double-submitting the *same* dataset's generation
  (protects the daily model quota), which is not the same thing as rate
  limiting across users. `DEPLOYMENT_ENV=hosted` exists as a config value
  with no protection behind it - see [Security Notes](#security-notes).
- **A frontend test suite.** None exists; backend coverage only.
- **CI/CD and Docker.** No `.github/workflows`, no Dockerfile, no
  docker-compose file anywhere in this repository.
- **BigQuery, WebSockets.** No reference to either anywhere in the codebase;
  not part of this architecture.

The full reasoning behind each "not building" decision, and what would have
to change for any of them to come back into scope, is in
[`docs/not-building.md`](docs/not-building.md). A more detailed status table
and the remaining backlog, ranked, is in
[`docs/srs-status.md`](docs/srs-status.md).

## Architecture

```
  React / Vite (TypeScript)
          |
          v  fetch, JSON over HTTP
  FastAPI  (backend/app/main.py)
          |
          v
  CSV ingestion            backend/app/ingest.py
  (stream size check, duplicate-header check, parse, shape check, memory check)
          |
          v
  Profiler                 backend/app/profiler.py, dtypes.py, leakage.py, metrics.py
  (per-column stats, task inference, metric selection - all deterministic)
          |
          v
  ProfileCard               backend/app/models.py
  (the ONLY object the LLM layer ever sees - never a DataFrame)
          |
          v
  LLM provider               backend/app/llm.py, prompts.py
  (Gemini, structured output, key rotation, one repair attempt)
          |
          v
  GenResult                 backend/app/models.py
  (strategy fields, THEN code - field order is load-bearing)
          |
          v
  Static validation          backend/app/validation.py
  (AST-only: parses, checks, never executes)
          |
          v
  React screens               frontend/src/screens/
  (Upload -> Target -> Profile -> Strategy -> Pipeline)
```

The core rule that shapes every layer above: **Python computes facts, the LLM
reasons over facts, the LLM never sees raw data.** `llm.py`'s entry point
accepts a `ProfileCard`, never a `DataFrame` - that function signature is the
literal enforcement point for the rule, not just a description of it.

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python (`requires-python >=3.12`), FastAPI `>=0.115`, Pydantic v2 `>=2.9`, pydantic-settings `>=2.6` | Verified running on Python 3.14.2 in this environment |
| Data | pandas `>=2.2,<3`, numpy `>=2.1` | pandas capped below 3.0: pandas 3 defaults string columns to a real `str` dtype rather than `object`, which breaks the dtype-classification ladder |
| LLM | `google-genai>=1.0`, model `gemini-3.1-flash-lite` (configurable) | The unified SDK - **not** the deprecated `google-generativeai` |
| Storage | `sqlite3` (Python stdlib), WAL mode | No ORM; one table for datasets, one for generation attempts |
| Frontend | React 18.3, Vite 5.4, TypeScript 5.6 (strict), Tailwind CSS v4 | Tailwind is configured through an `@theme` block in `src/index.css`, not a `tailwind.config.js` file. No React Router - a small hand-written History API wrapper (`src/routes.ts`) does URL routing |
| Frontend deps | `react-dropzone`, `shiki` (syntax highlighting, fine-grained core API only), `framer-motion`, `lucide-react` | No component library, no shadcn, no `@/` alias |
| Backend dev tooling | pytest `>=8.3`, pytest-asyncio, httpx, ruff `>=0.7` | `ruff check app tests` is clean |
| Frontend dev tooling | `tsc -b` (strict, `noUnusedLocals`, `noUnusedParameters`) | No test runner is configured |

Explicitly **not** used anywhere in this codebase, by rule in
[`CLAUDE.md`](CLAUDE.md): LangChain, LangGraph, Instructor, ydata-profiling,
Redis, Celery, SQLAlchemy, pyarrow.

## Project Structure

```
backend/
  app/
    main.py           FastAPI app factory, CORS, the one error-envelope handler
    api/datasets.py   The six HTTP routes (see API below)
    config.py         Settings from environment, the local-execution boot guard
    models.py         Every Pydantic schema - the contract between every layer
    errors.py         ErrorCode enum + status/retryability table, one place
    ingest.py         CSV streaming, validation, and rejection rules
    dtypes.py         The 7-rung dtype classification ladder
    profiler.py       Builds a ProfileCard from a DataFrame
    leakage.py        The three target-association formulas (spearman/eta/purity)
    metrics.py        Deterministic metric selection from class balance
    heuristics.py     Every threshold in the app, as a named constant with a reason
    heuristics.md     Cross-cutting relationships between heuristics constants
    prompts.py        System prompt + ProfileCard -> LLM prompt serialization
    llm.py            LLMProvider protocol, GeminiProvider, key rotation, retry
    storage.py        SQLite persistence and the TTL sweeper
    validation.py      Twelve static checks on generated code
  tests/               212 tests: fixture-corpus-driven, cassette-backed LLM tests
  pyproject.toml
  .env.example

frontend/
  src/
    App.tsx            The one useReducer holding all app state; also routing
    routes.ts           URL <-> screen mapping (hand-rolled, no router library)
    state.ts             The reducer - a failed generation never clears the profile
    api.ts               fetch wrapper, unwraps the backend's error envelope
    types.ts              Hand-written mirror of backend/app/models.py
    index.css              Tailwind v4 @theme block - every design token
    screens/               UploadScreen, TargetScreen, ProfileScreen, StrategyScreen, CodeScreen, LandingScreen
    components/
      layout/             WorkflowShell (sidebar + stage nav), ActivityDialog, StageIntro
      upload/              Dropzone
      target/              ColumnTable, ColumnRow
      profile/            StatTile, MetricPanel, ClassBalanceChart, QualityChip, QualityInsights, SystemWarnings, TaskConfidenceToggle
      strategy/            PreprocessingStep, DroppedColumnsTable, CandidateModelCard
      pipeline/            CodeBlock, ValidationChecklist, ValidationCheckRow, UnexecutedNotice
      shared/              Button, Card, StatusBadge, ErrorPanel, RetryButton, icons
  package.json
  .env.example

docs/
  not-building.md                              Explicit scope boundary, with reasons
  srs-status.md                                Full status table + ranked remaining backlog
  development.md                                Local-dev gotchas, cassette rules, traps that have already bitten
  spike-01-gemini-structured-output.md          Why field order / nested schemas behave the way they do on Gemini
  Agentic_AutoML_Apple_HIG_Design_System.md     The frontend's governing design spec

IMPLEMENTATION_PLAN.md   Frozen architecture + the eight-stage build order this project followed
CLAUDE.md                 Binding rules for any contributor (human or AI) working in this repo
```

## Requirements

- **Python 3.12 or newer** (`backend/pyproject.toml` declares
  `requires-python = ">=3.12"`; this environment runs 3.14.2 and every
  dependency installs clean on it)
- **Node.js 18 or newer** (Vite 5's minimum; this environment runs Node 21)
- **npm** (the repo ships a `package-lock.json`; no pnpm/yarn lockfile exists)
- **A Google Gemini API key** - free tier is enough to run the app; get one
  at [Google AI Studio](https://aistudio.google.com/). Without a key, every
  route works except `POST /api/datasets/{id}/generate`, which needs one.
- macOS or Linux. Not tested on Windows; nothing in the code is
  platform-specific, but the setup commands below assume a POSIX shell.

## Installation

```bash
git clone <this-repository-url>
cd Tabular-Pipeline-Synthesis
```

### Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
```

Open `.env` and set at least `GOOGLE_API_KEY` to a real key. Every other
value in `.env.example` has a working default.

### Frontend

```bash
cd frontend
npm install
```

If port 8000 is already taken on your machine (common - it collides with
several other local dev tools), create `frontend/.env.local`:

```bash
echo "VITE_API_BASE=http://localhost:8001/api" > frontend/.env.local
```

and run the backend on the matching port in the next section, keeping
`CORS_ORIGINS` in the backend's `.env` in step with whatever origin the
frontend actually serves from.

## Environment Variables

### Backend (`backend/.env`, copied from `backend/.env.example`)

| Variable | Required | Description | Example |
|---|---|---|---|
| `GOOGLE_API_KEY` | Yes, for generation | Gemini API key. Every other route works without one. | `AIza...` |
| `GOOGLE_API_KEY1` / `GOOGLE_API_KEY2` / `GOOGLE_API_KEY3` | No | Extra keys. When more than one key is set, requests round-robin across them and a 429 fails over to the next. Keys from the *same* Google Cloud project share one daily quota bucket - this buys failover, not extra headroom. | `AIza...` |
| `LLM_MODEL` | No | Gemini model name. | `gemini-3.1-flash-lite` |
| `LLM_TIMEOUT_S` | No | Request timeout in seconds (converted to ms for the SDK; Gemini enforces roughly a 10s floor below which it 400s instead of timing out). | `60` |
| `DEPLOYMENT_ENV` | No | `local` or `hosted`. Governs the boot guard below. | `local` |
| `ENABLE_LOCAL_EXECUTION` | No | Currently gates nothing except a startup assertion - there is no execution feature built yet. The app refuses to start if this is `true` while `DEPLOYMENT_ENV` is not `local`. | `false` |
| `EXECUTION_TIMEOUT_S` | No | Reserved, unused. | `60` |
| `EXECUTION_SAMPLE_ROWS` | No | Reserved, unused. | `500` |
| `RUNNER_PYTHON` | No | Reserved, unused. | `.venv-runner/bin/python` |
| `UPLOAD_DIR` | No | Where uploaded CSVs are stored on disk. | `./data/uploads` |
| `DB_PATH` | No | SQLite file path. | `./data/app.db` |
| `DATASET_TTL_HOURS` | No | How long a dataset and its profile are kept before the hourly sweep deletes them. | `24` |
| `MAX_FILE_MB` | No | Upload size limit, enforced while streaming. | `50` |
| `MAX_COLS` | No | Maximum column count accepted at ingest. | `1000` |
| `CORS_ORIGINS` | No | Comma-separated list of allowed origins. | `http://localhost:5173` |

### Frontend (`frontend/.env.local`, not checked in - see `frontend/.env.example`)

| Variable | Required | Description | Example |
|---|---|---|---|
| `VITE_API_BASE` | No | Base URL the frontend calls. Defaults to `http://localhost:8000/api` in code. | `http://localhost:8001/api` |

`.env.example` files in this repository hold variable *names* only, never a
real value - that rule is enforced by hand, not by tooling, so do not commit a
real key into either example file. Real values live in `backend/.env` and
`frontend/.env.local`, both gitignored.

## Running Locally

Two terminals.

**Backend** (from `backend/`):

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

If port 8000 is taken, run on another port (e.g. `--port 8001`) and set
`VITE_API_BASE` accordingly, as described above.

**Frontend** (from `frontend/`):

```bash
npm run dev
```

Open **`http://localhost:5173`**. Use `localhost`, not `127.0.0.1` - the
backend's default CORS allowlist contains only `http://localhost:5173`, and a
mismatch surfaces in the browser as a CORS error even though the request
succeeded on the server.

Health check: `curl http://localhost:8000/api/health` should return
`{"status": "ok", "version": "..."}`.

## How to Use

1. **Upload a CSV.** Drag a file onto the dropzone, or click to browse. The
   backend rejects it up front, with a specific reason, if it is empty,
   header-only, has duplicate column names, has only one column, exceeds
   1000 columns, or exceeds 50MB.
2. **Pick the target column.** The one column you want to predict.
3. **Confirm, and review the profile.** Python computes every statistic on
   this screen: row/column counts, duplicate rows, missingness, the inferred
   task (classification or regression) and its confidence, the chosen
   evaluation metric and why, per-column flags (constant, high-cardinality,
   ID-like, potential leakage, and so on). If the target is a discrete
   number - a 1-5 rating, a count - the task is genuinely ambiguous and the
   screen offers an override. You can also exclude any feature column from
   the pipeline entirely before generating.
4. **Generate the strategy.** This is the one step that calls Gemini. You get
   back a plan: which columns get dropped and why, what preprocessing each
   retained column needs, two to four candidate models ranked by fit for
   this dataset, and how the result should be validated - all grounded in
   the profile, never in a number that was never measured.
5. **Review the pipeline code.** The strategy's code, with the twelve-check
   validation report shown above it, not below it. A banner states plainly
   that the pipeline has not been executed. Copy or download the code and
   run it yourself in your own environment.

## API

Base path: `/api`. Every non-2xx response has the shape
`{"error": {"code": str, "message": str, "retryable": bool, "details": {}}}`.

### `GET /health`

Liveness check. Returns `{"status": "ok", "version": "<app version>"}`.

### `POST /datasets`

Upload a CSV (`multipart/form-data`, field name `file`).

**Response** `201` `DatasetUploadResponse`:
```json
{"dataset_id": "uuid", "filename": "sales.csv", "n_rows": 1000,
 "n_columns": 12, "columns": ["id", "amount", "..."], "state": "pending"}
```

**Errors:** `FILE_TOO_LARGE` (413), `DATASET_TOO_LARGE_IN_MEMORY` (413),
`UNPARSEABLE_CSV` (422), `EMPTY_DATASET` (422), `HEADER_ONLY` (422),
`SINGLE_COLUMN` (422), `TOO_MANY_COLUMNS` (422), `DUPLICATE_COLUMNS` (422).

### `GET /datasets/{id}`

Everything on record for a dataset, including its stored profile if one
exists. The recovery path for a browser refresh - the other three POST
routes leave nothing a `GET` could otherwise reach.

**Response** `200` `DatasetDetail`: `dataset_id`, `filename`, `n_rows`,
`n_columns`, `columns`, `created_at`, `state` (`pending`|`complete`),
`task_was_overridden`, `profile` (`ProfileCard | null` - `null` before
`/profile` has run, which is a normal state, not an error).

**Errors:** `DATASET_EXPIRED` (410) - covers both an unknown id and one whose
24-hour TTL has passed; the two are deliberately indistinguishable to avoid
leaking whether a given UUID ever existed.

### `POST /datasets/{id}/profile`

**Request** `ProfileRequest`:
```json
{"target_column": "churned", "problem_type_override": null}
```
`problem_type_override` is optional and only accepted when it resolves a
genuine ambiguity (a discrete-numeric target); an override incoherent with
the target's actual type is refused.

**Response** `200` `ProfileResponse`: `{"state": "complete", "profile": ProfileCard}`.
Persists the profile server-side so `/generate` can read it back.

**Errors:** `DATASET_EXPIRED` (410), `TARGET_NOT_FOUND` (422),
`TARGET_ALL_NULL` (422), `TARGET_SINGLE_VALUE` (422),
`TARGET_TYPE_UNSUPPORTED` (422) - the target's dtype (text, datetime, or a
column with no usable values) has no corresponding problem type, or the
requested override is incoherent with it.

### `POST /datasets/{id}/generate`

**Request** `GenerateRequest`:
```json
{"excluded_columns": ["notes", "internal_id"]}
```
Deliberately carries no profile data - the server always reads back what
`/profile` already stored, never a client-supplied one. `excluded_columns`
is an instruction ("do not offer this column to the model"), not a fact
claim, so it does not violate that rule; every name is validated against the
stored profile and the target column cannot be excluded.

**Response** `200` `GenerateResponse`: `{"state": "complete", "result": GenResult, "validation": ValidationReport}`.
A failing validation report is still returned alongside the code - never
suppressed.

**Errors:** `DATASET_EXPIRED` (410, dataset not profiled yet or aged out),
`TARGET_NOT_FOUND` (422, an excluded-column name does not exist),
`TARGET_SINGLE_VALUE` (422, an attempt to exclude the target column),
`LLM_RATE_LIMITED` (429, all configured keys exhausted, or a generation is
already in flight for this dataset), `LLM_TIMEOUT` (504),
`LLM_UNAVAILABLE` (503), `LLM_INVALID_OUTPUT` (502, the model's output could
not be parsed even after one repair attempt).

### `GET /datasets/{id}/usage`

Every recorded provider attempt for a dataset - successes, failures, and the
repair round - with real measured tokens and latency. Not a quality metric
for the generated pipeline; there is no such metric anywhere in this API.

**Response** `200` `UsageResponse`: `dataset_id`, `attempts: GenerationAttempt[]`,
`total_attempts`, `total_input_tokens`, `total_output_tokens`.

**Errors:** `DATASET_EXPIRED` (410).

## Profiling

Everything on the Profile screen is computed by `backend/app/profiler.py` and
its supporting modules - no model call is involved anywhere in this stage.
Every named threshold below lives in `heuristics.py` as a constant with a
written justification; nothing here is a number chosen ad hoc in the code
that uses it.

**Per column:** inferred type (via a seven-rung classification ladder -
boolean vocabulary, native numeric dtype, datetime parse rate, numeric-string
coercion, near-unique text, categorical fallback, unknown), missing
count/percentage, unique count/percentage, the share held by the single most
common value, up to five sample level names (low-cardinality categoricals
only, capped and truncated - the one place file content reaches the LLM
prompt, treated as metadata rather than data), min/max/mean/std/median for
numeric columns, and flags: `all_missing`, `high_missing` (>50% null),
`constant`, `quasi_constant` (one value holds ≥99% of rows, never applied to
the target), `id_like` (≥99% unique), `high_cardinality` (>50 distinct
values, or >50% of row count, whichever fires first, categorical columns
only), `numeric_as_string`, `potential_leakage`.

**Target association / leakage:** every feature column gets a single
association score against the target, using whichever of three formulas fits
its type and the task - Spearman rank correlation (numeric feature,
regression target), a correlation ratio / eta statistic (numeric-categorical
or categorical-numeric pairs), or a hand-defined level-purity score
(categorical feature, classification target). All three return an absolute
value in `[0, 1]`; a score above `0.98` sets the `potential_leakage` flag.
Free text, datetime, and unknown-type columns are skipped entirely - "no
meaningful test applies" is recorded as `association_method: "none"`, the
same value used when a test was attempted but too little paired data
survived.

**Task inference:** deterministic from the target column's inferred type.
Boolean or two-level categorical -> binary classification; categorical with
more levels -> multiclass; continuous numeric -> regression; **discrete**
numeric (a rating, a small count) is the one genuinely ambiguous case, and
gets a lower confidence score plus a UI offer to override it explicitly.

**Metric selection:** regression always uses RMSE (secondary: MAE, R²);
multiclass always uses F1-macro (secondary: accuracy); binary classification
picks accuracy, F1, or PR-AUC by the majority:minority class ratio -
`≤1.5:1` accuracy, `≤10:1` F1, above that PR-AUC - with ROC-AUC always listed
as a secondary and never selectable as the primary metric under imbalance.

**Sampling:** every per-column statistic above is always computed on the full
file. The one exception is the leakage-association pass, an O(rows ×
columns) operation - above 200,000 rows it runs on one shared random sample
(same rows for every column, fixed seed), and `profiled_on_sample` /
`sample_rows` are set honestly and shown on the profile screen whenever it
happens. Cardinality-related flags are never computed on a sample, because
sampling systematically distorts unique-value counts.

## LLM Architecture

**Provider:** Google Gemini, via the `google-genai` SDK, default model
`gemini-3.1-flash-lite` (configurable via `LLM_MODEL`).

**What crosses the boundary to the model - and nothing else:** the serialized
`ProfileCard` - filename, row/column counts, the target column name, the
inferred task and its confidence, the primary and secondary metrics, class
balance, duplicate row count, and the per-column statistics listed under
[Profiling](#profiling) above. **Raw dataset rows are never sent.** The only
values from the actual file that reach the prompt at all are column names and
the capped low-cardinality sample level names described above - and the
prompt explicitly instructs the model to treat both as inert data, never as
instructions, as a prompt-injection defence.

**Structured output:** the response is constrained to the `GenResult` Pydantic
schema via Gemini's `response_schema` parameter, not parsed out of free text.
`GenResult`'s field order is declared deliberately - every strategy decision
(problem type, target, metric, drops, preprocessing, candidate models,
validation approach, summary, risks) precedes the `code` field, so the model
commits to a plan before writing the pipeline that implements it. See
[`docs/spike-01-gemini-structured-output.md`](docs/spike-01-gemini-structured-output.md)
for the empirical verification that Gemini actually preserves this ordering.

**Reliability:** requests round-robin across up to four configured API keys;
a 429 fails over to the next key, other provider errors (timeout,
unavailable) do not rotate and fail immediately. If the model's JSON response
fails schema validation, exactly one automated repair attempt is made, with
the validation error appended to the prompt asking for a complete corrected
response. A provider-level failure (rate limit, timeout, unavailable) is
never retried automatically - it surfaces to the user with a retry button
where the error code says it is safe to press. Every attempt, successful or
not, is logged with real token counts and latency to a `generations` table,
readable via `GET /datasets/{id}/usage`.

## Validation

Twelve checks run against every generated result, all static - none of them
execute the code. If the code fails to parse, only the two checks that read
`GenResult`/`ProfileCard` directly still run; every AST-based check is
skipped rather than reported as passing.

| Check | Severity | Catches |
|---|---|---|
| `syntax_compile` | Error | The code fails to `compile()` - a syntax error |
| `ast_import_allowlist` | Error | Any import outside pandas, numpy, or scikit-learn |
| `dangerous_calls` | Error | Calls to `eval`, `exec`, `compile`, `__import__`, `os.system`, or anything rooted at `subprocess`, `socket`, `requests`, `urllib` |
| `hallucinated_columns` | Error | A string used as a column reference that is not a real profile column, not self-defined by the code, and close enough to a real name (fuzzy-match ratio ≥0.85) to be a plausible typo rather than an engineered feature name |
| `target_column_referenced` | Error | The target column name never appears anywhere in the code |
| `gen_result_self_consistency` | Error | The strategy's stated problem type, target column, or primary metric does not match what the profiler computed |
| `pipeline_or_column_transformer` | Warning | No `Pipeline` or `ColumnTransformer` used anywhere |
| `random_state_set` | Warning | No `random_state` keyword argument appears anywhere in the code |
| `split_or_cross_validation` | Warning | No train/test split or cross-validation call of any kind |
| `primary_metric_computed` | Warning | The chosen primary metric's keyword never appears in the code |
| `declared_columns_exist` | Warning | A column named in the strategy's drop list or preprocessing steps does not exist in the profile |
| `dropped_columns_not_referenced` | Warning | A column the strategy (or the user, via `excluded_columns`) declared dropped is still used as a feature in the code |

A report `passed` only when every **error**-severity check passed; warnings
never fail the overall report. The report is returned alongside the code
regardless of outcome - a failing check is never used to hide the code from
the user, only to inform the decision about whether to trust it.

## SRS Implementation Status

No standalone SRS exists in this repository - see
[Current Status](#current-status) above for what that means for this table.
Grouped by the phase each item was planned in
([`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) stages 0-5 = MVP-1;
stage 6 = MVP-1.5; unplanned items from
[`docs/srs-status.md`](docs/srs-status.md)'s backlog are marked Phase 2).

### MVP-1

| Feature | Status | Notes |
|---|---|---|
| CSV upload + validation | ✅ Complete | `ingest.py`, 7 rejection codes |
| Target selection | ✅ Complete | |
| Target/task override | ✅ Complete | Discrete-numeric ambiguity only |
| Feature exclusion | ✅ Complete | `excluded_columns` |
| Task inference | ✅ Complete | `dtypes.py` + `profiler.py` |
| Deterministic profiling | ✅ Complete | See [Profiling](#profiling) |
| Metric selection | ✅ Complete | `metrics.py` |
| Metric override | ❌ Not implemented | Only task type is overridable |
| LLM strategy + code generation | ✅ Complete | Structured output, `GenResult` |
| Static validation (12 checks) | ✅ Complete | See [Validation](#validation) |
| 5-screen frontend | ✅ Complete | Incl. real URLs, session recovery |
| Dataset/profile recovery (`GET`) | ✅ Complete | |
| Usage/quota visibility | ✅ Complete | |
| Repair-on-schema-failure | ✅ Complete | One automatic retry |
| Repair-on-failed-check loop | ❌ Not implemented | `VALIDATION_FAILED` reserved, never raised |
| Frontend test suite | ❌ Not implemented | Backend only (212 tests) |

### MVP-1.5

| Feature | Status | Notes |
|---|---|---|
| Local subprocess execution | ❌ Not implemented | Config flags exist, gate nothing |
| `.venv-runner` + scikit-learn runner | ❌ Not implemented | Not a backend dependency |
| Executed-on-a-sample result display | ❌ Not implemented | Depends on the above |

### Phase 2 / explicitly deferred

| Feature | Status | Notes |
|---|---|---|
| Async jobs + polling | ❌ Not implemented (decided against for now) | `JobState` narrowed to 2 members after the 6-member version was found to never transition |
| Distribution/histogram data | ❌ Not implemented | Designed, not built - see `docs/srs-status.md` |
| Auth / multi-user rate limiting | ❌ Not implemented | Hard blocker before any non-local deployment |
| Docker execution sandbox | ❌ Not implemented | Phase 2 of stage 6 |
| CI/CD | ❌ Not implemented | No workflow files anywhere |
| Multi-target prediction | ❌ Not building | See `docs/not-building.md` #2 |
| Unsupervised learning | ❌ Not building | See `docs/not-building.md` #3 |
| User-chosen algorithms/preprocessing | ❌ Not building | See `docs/not-building.md` #4-5 |
| Formats other than CSV | ❌ Not building | See `docs/not-building.md` #11 |

Full reasoning and a ranked recommendation order for the still-open items is
in [`docs/srs-status.md`](docs/srs-status.md).

## Known Limitations

Stated plainly, not as a footnote:

- **CSV only.** No Excel, Parquet, JSON, or database connections.
- **One target column at a time.** No multi-output or multi-label prediction.
- **Supervised learning only.** No clustering, no anomaly detection.
- **The generated code is never executed by this app**, in any version
  currently in this repository. You run it yourself, in your own
  environment. There is no accuracy figure, no leaderboard, and no "best
  model" claim anywhere in the product - by design, not by omission.
- **No authentication and no multi-user rate limiting.** This is a
  local-development tool as it stands. `DEPLOYMENT_ENV=hosted` is a config
  value with no protection wired up behind it - do not put this on the
  public internet as-is.
- **No accounts, no history.** Datasets are anonymous UUIDs, deleted after
  `DATASET_TTL_HOURS` (24h default).
- **Gemini's free tier caps generation at 20 requests/day, per project, per
  model.** Configuring multiple `GOOGLE_API_KEY*` values from the *same*
  Google Cloud project buys failover on a 429, not extra quota. Switching
  `LLM_MODEL` grants a fresh bucket if one is exhausted mid-session.
- **No frontend test suite** and no CI/CD pipeline of any kind.
- **A dev-only dependency vulnerability is currently present and
  unaddressed:** `npm audit` reports a moderate esbuild advisory
  (GHSA-67mh-4wv8-2f99) via Vite 5's bundled esbuild - it allows a malicious
  website to read responses from the Vite dev server while it is running.
  Fixing it requires an unreleased-as-tested Vite 8 major upgrade
  (`npm audit fix --force`), which this cleanup pass deliberately did not
  attempt. It affects `npm run dev` only, not the production build.

## Roadmap

Ranked by the order recommended in
[`docs/srs-status.md`](docs/srs-status.md), grouped so a cassette
re-recording (see [Testing](#testing)) only has to happen once per phase:

1. **Distribution/chart data** - a new, separate endpoint and storage column,
   deliberately kept off `ProfileCard` so it never reaches the LLM prompt or
   invalidates the recorded test cassettes.
2. **Large-dataset sampling fixture** - close the untested-at-scale gap on
   the 200,000-row sampling path.
3. **Repair-on-failed-check loop** - use the reserved `VALIDATION_FAILED`
   code for real, retrying generation once against the specific checks that
   failed rather than only against a schema error.
4. **MVP-1.5 local execution** - `LocalSubprocessSandbox`, a separate
   `.venv-runner` with scikit-learn, a 500-row sample run with a hard
   timeout, gated by `ENABLE_LOCAL_EXECUTION` and the existing boot guard.
5. **Docker sandbox boundary** - only after local execution is proven out.
6. **Auth and rate limiting** - not optional the moment this leaves
   localhost; the first thing built if that day comes, not the last.

## Testing

**Backend:**

```bash
cd backend
.venv/bin/python -m pytest        # 212 passed, as of this writing
.venv/bin/ruff check app tests    # clean, as of this writing
```

Tests are fixture-corpus-driven: profiler and validator changes require a
named fixture CSV (`tests/fixtures/`) or a code-string fixture
(`tests/fixtures/validation_corpus.py`) demonstrating the specific behaviour,
and assertions check structural invariants, never exact LLM prose.

**LLM tests run offline.** `backend/tests/cassettes/*.json` holds three real
recorded Gemini responses, keyed by a hash of the exact prompt text. Any
change to `ColumnProfile`, `ProfileCard`, or `prompts.py` invalidates all
three and the affected tests fail with `FileNotFoundError` - `test_prompts.py`
asserts the prompt's structure independently and is the intended tripwire,
firing before a cassette miss would. Re-recording costs real Gemini quota, so
it should be a deliberate, batched action, not incidental to unrelated work.

**Frontend:**

```bash
cd frontend
npx tsc -b        # strict typecheck
npm run build     # runs tsc, then the production Vite build
```

No frontend test runner is configured. UI changes in this project have been
verified by hand against the running dev server; there is no automated
frontend regression suite to point to.

## Security Notes

- **Generated code is never executed by this application**, in this or any
  prior version currently in the repository. The twelve checks in
  [Validation](#validation) are static analysis only - they reduce the
  chance that code you choose to run yourself does something obviously
  unsafe, but they are not a sandbox and were never designed as one.
- **`ENABLE_LOCAL_EXECUTION` exists in config but is inert** - there is no
  execution module for it to gate yet. If a future version adds one, the
  existing boot guard already refuses to start with local execution enabled
  outside `DEPLOYMENT_ENV=local`, which is the correct default for running
  arbitrary generated code without a container boundary.
- **No authentication.** Every route is open to anyone who can reach the
  process. Dataset IDs are UUIDs, not guessable, but nothing stops an
  authenticated-adjacent actor with network access from reading or
  generating against any dataset ID they observe.
- **Prompt injection is a considered threat, not an oversight.** The only
  user-controlled text that reaches the LLM prompt is column names and a
  small number of capped, truncated category-level names; the system prompt
  explicitly instructs the model to treat all of it as inert data, never as
  instructions, and to flag anything suspicious in the `risks` field rather
  than act on it.
- **A dev-only npm advisory is currently open** - see
  [Known Limitations](#known-limitations).
- **Do not deploy this as-is beyond localhost.** `DEPLOYMENT_ENV=hosted` is a
  recognized config value with no protection implemented behind it yet.

## Contributing / Development

Read [`CLAUDE.md`](CLAUDE.md) first - it is the binding rule set for this
repository (dependency constraints, the prompt-surface-vs-comment split in
`models.py`, why `GenResult`'s field order must not change, testing
requirements). Local-dev gotchas that have already cost time once - CORS
between `localhost` and `127.0.0.1`, the Gemini timeout floor, cassette
invalidation, async task garbage collection - are catalogued in
[`docs/development.md`](docs/development.md) so they only cost time once.

Before proposing a feature, check
[`docs/not-building.md`](docs/not-building.md) - a proposal that appears
there is closed until that file is edited with a reason, not quietly built
around it.

## License

No license file is present in this repository. Treat the code as
all-rights-reserved by default unless the repository owner adds one.
