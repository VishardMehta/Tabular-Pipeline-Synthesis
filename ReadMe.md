# Agentic AutoML

Upload a tabular CSV, get a profile computed in Python and a modelling pipeline
written by an LLM that reasons only over that profile. The generated code is
never executed in MVP-1, so no score shown anywhere in this tool is a measured
result.

Architecture is frozen in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
Working rules for contributors and for Claude Code are in [CLAUDE.md](CLAUDE.md).

## Status

Stage 0, the walking skeleton. The schemas and the HTTP contract are final; the
three dataset routes return fixtures rather than real results. Stages 1 through
7 fill in the bodies without changing the shapes.

## Local setup

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

Checks:

```bash
cd backend  && .venv/bin/ruff check app tests && .venv/bin/python -m pytest
cd frontend && npm run build     # runs tsc first
```

## Environment notes

These are properties of this machine, not requirements of the project.

- **Interpreter is Python 3.14.2.** The project declares `requires-python =
  ">=3.12"`. 3.14 was the only interpreter available and every dependency
  installs and runs clean on it. Stage 6 needs scikit-learn and xgboost in a
  separate runner venv at `.venv-runner/`, and their 3.14 wheel coverage may be
  thinner. If that bites, the runner venv can pin a different Python version.
  It is a separate process, so nothing else has to change.
- **pandas is pinned `>=2.2,<3`.** pandas 3.0 defaults string columns to a real
  `str` dtype rather than `object`, which breaks the stage-2 dtype ladder, and
  the LLM writes 2.x idiom from its training data. The runner venv must carry
  the identical pin so the profiler and the executed code agree about the file.
- **Port 8000 may be occupied.** Another local service holds it on this machine.
  Run the API on a different port and point the frontend at it with
  `VITE_API_BASE` in `frontend/.env.local`, keeping `CORS_ORIGINS` in step.
