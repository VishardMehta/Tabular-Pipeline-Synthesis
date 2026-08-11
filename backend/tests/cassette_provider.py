"""Cassette playback for LLM tests. Zero network, zero quota.

A cassette is one recorded response, keyed by a hash of the exact prompt that
produced it. Recording happens once, out of band, by running
record_cassettes.py with a real GOOGLE_API_KEY - never as a side effect of
running the test suite.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.llm import RawGeneration

CASSETTE_DIR = Path(__file__).parent / "cassettes"


def cassette_key(system_prompt: str, user_message: str) -> str:
    """The same key record_cassettes.py uses to name a cassette file.

    Hashing the exact prompt, not the profile it was built from, is what
    makes this catch a prompt change: editing SYSTEM_PROMPT or
    build_user_message changes the hash, and the old cassette silently stops
    matching instead of replaying a response to a prompt that no longer
    exists.
    """
    digest = hashlib.sha256(f"{system_prompt}\n---\n{user_message}".encode()).hexdigest()
    return digest[:16]


class CassetteProvider:
    """Replays the recorded response for a given prompt.

    Raises plainly when no cassette matches, rather than falling through to
    a real call - a test suite that silently hits the network on a cache
    miss is the failure mode cassettes exist to prevent.
    """

    name = "cassette"

    def __init__(self, model: str = "gemini-3.6-flash") -> None:
        self.model = model

    def generate(self, *, system_prompt: str, user_message: str) -> RawGeneration:
        key = cassette_key(system_prompt, user_message)
        path = CASSETTE_DIR / f"{key}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"No cassette for this prompt ({key}.json). Run "
                "backend/tests/record_cassettes.py with GOOGLE_API_KEY set to record it."
            )
        payload = json.loads(path.read_text())
        return RawGeneration(
            text=payload["raw_text"],
            input_tokens=payload.get("input_tokens"),
            output_tokens=payload.get("output_tokens"),
        )
