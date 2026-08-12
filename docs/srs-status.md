# SRS implementation status

This repository has no standalone SRS or design document committed to it.
`IMPLEMENTATION_PLAN.md:300` references "the SRS" as the source the
[not-building list](not-building.md) exists to test proposals against, but
that source document itself was never checked in - it lived in an external
"final blueprint" the plan was built from. This file, `not-building.md`, and
`IMPLEMENTATION_PLAN.md` together are the closest thing to a requirements
record this repository has, and this table is measured against them, not
against a file that does not exist here.

This file supersedes an earlier `docs/backend-refinement-plan.md`. That
document proposed eleven numbered recommendations (R0-R11); most have since
been acted on. What follows is the current state and the backlog that
remains, not the original proposal document.

---

## Full status table

Status legend: ✅ Complete · 🟡 Partial · ❌ Not implemented · ❌* Not
implemented, deliberately (see `not-building.md`)

| Feature | Status | Current implementation | Remaining work |
|---|---|---|---|
| CSV upload, size/shape validation | ✅ | `ingest.py`: streamed size check, pre-pandas duplicate-header check, 7 rejection codes | - |
| Target column selection | ✅ | `ProfileRequest.target_column` | - |
| Target/task override | ✅ | `problem_type_override`, coherence-checked in `profiler._apply_task_override` | - |
| Feature exclusion | ✅ | `GenerateRequest.excluded_columns`, validated against the stored profile | - |
| Task inference (classification/regression) | ✅ | `dtypes.py` 7-rung ladder + `profiler._map_problem_type` | - |
| Dataset profiling (dtypes, missing, cardinality, duplicates) | ✅ | `profiler.py` | - |
| Class balance / imbalance detection | ✅ | `metrics.py::class_balance_ratio` | - |
| Leakage / target-association signal | ✅ | `leakage.py`, 3 formulas by type | - |
| Metric recommendation | ✅ | `metrics.py::select_metrics`, band-based | - |
| Metric override | ❌ | - | Not designed. Task override exists; metric is always re-derived from the (possibly overridden) task. Low priority - no reported need yet |
| LLM strategy generation | ✅ | `llm.py`, `prompts.py`, Gemini structured output | - |
| Structured `GenResult` (Pydantic response_schema) | ✅ | `models.py`, verified field-order preservation - see `spike-01` | - |
| Preprocessing strategy | ✅ | `GenResult.preprocessing`, LLM-authored, grounded in profile facts | - |
| Candidate model selection | ✅ | `GenResult.candidate_models`, 2-4, no score field | - |
| Validation-strategy description | ✅ | `GenResult.validation_strategy`, prose, not executed | - |
| Static code validation (12 checks) | ✅ | `validation.py` - see README's Validation section for the full list | - |
| Invented-column detection | ✅ | `hallucinated_columns` check, fuzzy-match against real names | - |
| Strategy/code self-consistency | ✅ | `gen_result_self_consistency` check | - |
| One automatic repair attempt (schema failure) | ✅ | `llm.py::generate`, `MAX_ATTEMPTS = 2` | - |
| Repair loop on a *failed validation check* | ❌ | `ErrorCode.VALIDATION_FAILED` reserved, never raised | Design a second LLM round that appends the specific failing checks (not just a schema error) and retries once. Ranked #3 below |
| Frontend 5-screen workflow | ✅ | `frontend/src/screens/` | - |
| Real per-screen URLs, back/forward | ✅ | `frontend/src/routes.ts`, hand-rolled History API | - |
| Dataset/profile recovery (`GET /datasets/{id}`) | ✅ | `api/datasets.py` | - |
| Usage/quota visibility (`GET .../usage`) | ✅ | `api/datasets.py`, real token/latency data | - |
| Execution of generated code | ❌ | No `execution.py`; scikit-learn not a backend dependency | Stage 6 / MVP-1.5, see below |
| Local subprocess sandbox | ❌ | `ENABLE_LOCAL_EXECUTION` gates only a boot assertion | Same |
| Docker execution sandbox | ❌ | Not designed in this repo | Phase 2 of stage 6, after local execution is proven |
| Model training / scores / comparison | ❌* | `GenResult` has no field capable of holding one | Not building until execution exists; even then the number must be labelled as measured on a sample |
| Feature importance | ❌ | Depends on execution | Not designed |
| Model download | ❌ | Depends on execution - no trained artifact exists anywhere | Not designed |
| Self-correction loop | 🟡 | See "repair on schema failure" above; no check-level repair | Same as above |
| Async jobs / progress polling | ❌ | `JobState` deliberately narrowed to `pending\|complete`; both routes are synchronous | Two honest paths: build it for real (job table, `GET /jobs/{id}`, real transitions), or leave both routes synchronous permanently. Leaving `JobState` half-built was the actual defect that was fixed - see `docs/development.md` |
| Distribution / histogram chart data | ❌ | `profiler.py` computes full `value_counts()` per column, keeps only the top 5 | Ranked #1 below - designed, not built |
| BigQuery | ❌ | No reference anywhere in the codebase | Not part of this architecture; would need its own design if ever proposed |
| WebSocket | ❌ | REST/HTTP only | Not needed unless async jobs are built |
| Authentication | ❌ | No auth anywhere in the API | Hard blocker before any non-local deployment - ranked last below, deliberately |
| Rate limiting (multi-user) | ❌ | An in-process single-generation-per-dataset guard exists (`api/datasets.py::_single_generation`) - this protects the daily model quota from a double-click, not from multiple users | Same as authentication |
| Database persistence | ✅ | SQLite, `storage.py` | - |
| SQLite WAL mode | ✅ | `storage.py::connect` sets `PRAGMA journal_mode=WAL` | - |
| TTL cleanup | ✅ | Hourly sweep + boot-time sweep, `DATASET_TTL_HOURS` | - |
| Backend test suite | ✅ | 212 tests, pytest, fixture-corpus-driven | - |
| Large-dataset sampling coverage | 🟡 | Sampling logic exists and is used above 200,000 rows; no fixture that size exists, so the path is covered by construction, not by test | Ranked #2 below |
| Frontend test suite | ❌ | None | Not started |
| Security testing | 🟡 | AST-based static validation (import allowlist, dangerous-call denylist) exists for generated code; no dependency scanning, no auth, no formal pen test | See Security Notes in README |
| Performance / load testing | ❌ | None | Not started |
| CI/CD | ❌ | No `.github/workflows`, no other CI config | Not started |
| Deployment tooling (Docker, compose) | ❌ | No Dockerfile or compose file anywhere in the repo | Not started |
| Multi-target prediction | ❌* | - | Deliberately out - see `not-building.md` #2 |
| Unsupervised learning | ❌* | - | Deliberately out - see `not-building.md` #3 |
| User-chosen algorithms/hyperparameters | ❌* | - | Deliberately out - see `not-building.md` #4 |
| User-chosen preprocessing steps | ❌* | - | Deliberately out - see `not-building.md` #5 |
| Client-supplied `ProfileCard` | ❌* | Explicitly forbidden as a security boundary | See `not-building.md` #6 |
| In-browser code editing | ❌* | - | Deliberately out - see `not-building.md` #7 |
| Chat / conversational refinement | ❌* | - | Deliberately out - see `not-building.md` #8 |
| Accounts, projects, history, sharing | ❌* | - | Deliberately out - see `not-building.md` #9 |
| Formats other than CSV | ❌* | - | Deliberately out - see `not-building.md` #11 |
| Streaming/chunked profiling | ❌* | Files are capped and read whole; sampling (not streaming) handles large row counts | See `not-building.md` #12 |
| Model/provider choice exposed to the user | ❌* | `LLM_MODEL` is deployment config, not a user setting | See `not-building.md` #13 |
| Prompt customization by the user | ❌* | - | Deliberately out - see `not-building.md` #14 |

---

## Ranked remaining work

In recommended order. Grouped so a cassette re-recording (see
`docs/development.md`) happens at most once per phase.

1. **Distribution / histogram chart data.** `profiler.py` already computes a
   full `value_counts()` per column and discards everything past the top 5.
   Must **not** be added to `ColumnProfile` - that field is prompt surface,
   and adding per-level counts to it would both bloat every prompt and push
   near-raw data at the LLM against the core rule. Correct shape: a separate
   module, a separate storage column, a separate `GET .../distributions`
   endpoint, computed from the same in-memory frame `/profile` already
   parsed. Zero cassette risk if `ColumnProfile` is genuinely left alone.
2. **Large-dataset sampling fixture.** Generate a >200,000-row fixture at
   test time (numpy, fixed seed - cheap) to exercise the sampled leakage-
   correlation path for real, closing the largest untested code path in the
   profiler.
3. **Repair-on-failed-check loop.** Use `ErrorCode.VALIDATION_FAILED` for
   real: when the static checks fail, retry generation once with the
   specific failing checks appended to the prompt, distinct from today's
   schema-validation-only repair attempt.
4. **MVP-1.5 local execution.** `LocalSubprocessSandbox` implementing a
   `Sandbox` protocol, a separate `.venv-runner/` with scikit-learn (kept out
   of the API's own environment on purpose - that separation is what makes
   the later Docker boundary an obvious next step rather than a rewrite), a
   500-row sample written alongside the code, `subprocess.run` with a
   timeout, process-group kill on timeout expiry. Gated by
   `ENABLE_LOCAL_EXECUTION`, which already boot-guards this correctly.
5. **Docker execution sandbox.** Only after step 4 is proven out against
   real generated code, not before.
6. **Authentication and rate limiting.** Deliberately last, and deliberately
   not optional the moment this leaves localhost - `DEPLOYMENT_ENV=hosted`
   should not be reachable in practice until this exists.

## Explicitly not recommended

| Proposal | Why not |
|---|---|
| Multi-target prediction | Touches `problem_type`, `task_confidence`, `primary_metric`, and `class_balance_ratio` on every profile - turns `target_association` from a scalar into a matrix. Changes the prompt, therefore invalidates all three cassettes, for a need that is genuinely niche against "give a defensible starting pipeline" |
| User-chosen algorithms or hyperparameters | The model choosing an approach *and justifying it against the profile* is the product. A dropdown of estimators makes this a form with an LLM attached |
| User-chosen preprocessing steps | Same reasoning, and `PreprocessingStep.step` is free text rather than an enum - there is no fixed vocabulary to expose as a UI control even if this were wanted |
| Accepting a client-supplied `ProfileCard` | Permanently forbidden - a caller who can edit the profile can make the model justify any pipeline, and the self-consistency check would still pass because it compares the result against the same forged profile |
| Any metric/score value on `GenResult` | Forbidden by `CLAUDE.md`. No execution means any number here would be fabricated, and it would render with the same formatting as a measured one |
| Executing generated code in the API process | The separate runner venv and subprocess boundary exist specifically so execution is never in-process |
