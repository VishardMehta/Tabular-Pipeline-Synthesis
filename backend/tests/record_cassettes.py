"""Records real Gemini responses into tests/cassettes/, once.

Not a pytest test - a manual script, run by a developer with a real
GOOGLE_API_KEY in the environment. The test suite itself never calls this and
never touches the network; see cassette_provider.py for the replay side.

Usage:
    cd backend && .venv/bin/python -m tests.record_cassettes

Recording happens against the same three fixtures used for the live
validation pass in the previous session (leaking_feature.csv,
skewed_regression.csv, high_cardinality_categorical.csv), so the first real
llm.py response and the prompt's last live-validated behaviour are the same
three datasets.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import profiler, prompts
from app.config import settings
from app.llm import GeminiProvider
from tests.cassette_provider import CASSETTE_DIR, cassette_key

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "profiler"

# (filename, target_column). All three carry a target column literally named
# "target"; see the CSVs themselves.
FIXTURES = [
    ("leaking_feature.csv", "target"),
    ("skewed_regression.csv", "target"),
    ("high_cardinality_categorical.csv", "target"),
]


def record(filename: str, target_column: str, provider: GeminiProvider) -> None:
    frame = pd.read_csv(FIXTURES_DIR / filename, engine="c")
    card = profiler.profile(frame, f"cassette-{filename}", filename, target_column)

    system_prompt = prompts.SYSTEM_PROMPT
    user_message = prompts.build_user_message(card)
    key = cassette_key(system_prompt, user_message)
    path = CASSETTE_DIR / f"{key}.json"

    if path.exists():
        print(f"skip  {filename}: cassette {key}.json already recorded")
        return

    print(f"call  {filename}: requesting a live generation...")
    started = time.monotonic()
    raw = provider.generate(system_prompt=system_prompt, user_message=user_message)
    latency_ms = int((time.monotonic() - started) * 1000)

    CASSETTE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "fixture": filename,
                "model": provider.model,
                "raw_text": raw.text,
                "input_tokens": raw.input_tokens,
                "output_tokens": raw.output_tokens,
                "latency_ms": latency_ms,
                "recorded_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
    )
    print(f"saved {filename} -> {path.name} ({latency_ms} ms, {len(raw.text)} chars)")


def main() -> None:
    if not settings.google_api_key:
        raise SystemExit(
            "GOOGLE_API_KEY is not set. Cassettes must be recorded against a real key."
        )

    provider = GeminiProvider(
        api_key=settings.google_api_key,
        model=settings.llm_model,
        timeout_s=settings.llm_timeout_s,
    )
    for filename, target_column in FIXTURES:
        record(filename, target_column, provider)


if __name__ == "__main__":
    main()
