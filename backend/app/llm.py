"""The LLM provider layer.

Not prompt surface, except for _REPAIR_NOTE below. Every other string here is
plumbing: talking to Gemini, mapping every failure to an existing errors.py
code, and retrying once when the model's own output fails to validate.

prompts.py is frozen for this session - the prompt in it was authored and
live-validated last session, and this module must not "improve" it. The
retry-with-repair flow did not exist when that file was written, so its one
new fragment of prompt text is appended at the call site here instead of
touching prompts.py.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Protocol

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import ValidationError

from app import prompts, storage
from app.config import settings
from app.errors import AppError, ErrorCode
from app.models import GenResult, ProfileCard

# The first response, plus one repair attempt if it fails to validate. A
# third try spends quota chasing a prompt-shaped problem that one repair pass
# either fixes or does not; a validation error stated once and ignored twice
# is not going to be fixed by asking a third time in the same words.
MAX_ATTEMPTS = 2

# New prompt text, not in prompts.py - see the module docstring for why.
_REPAIR_NOTE = """
Your previous response did not validate against the required schema. Produce
the complete, corrected result again in full - not a partial patch and not a
diff, the whole object - fixing the problem named below.

Validation error:
{error}
""".strip()


@dataclass(frozen=True)
class RawGeneration:
    """One provider call's output, before it is parsed as a GenResult."""

    text: str
    input_tokens: int | None
    output_tokens: int | None


class LLMProvider(Protocol):
    """A source of raw GenResult JSON text for one prompt.

    Implementations raise AppError directly for provider-level failure -
    rate limit, unavailable, timeout - so `generate()` below never has to know
    which provider it is talking to. A ValidationError is not a provider
    failure and is never raised here; parsing the text is the caller's job.
    """

    name: str
    model: str

    def generate(self, *, system_prompt: str, user_message: str) -> RawGeneration: ...


class GeminiProvider:
    """Talks to Gemini through google-genai.

    Nested models, field ordering and 503-as-routine are all measured
    behaviour, not assumptions - see docs/spike-01-gemini-structured-output.md.
    """

    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_s: int) -> None:
        self.model = model
        self._client = genai.Client(api_key=api_key)
        # HttpOptions.timeout is milliseconds; LLM_TIMEOUT_S in .env is seconds.
        self._timeout_ms = timeout_s * 1000

    def generate(self, *, system_prompt: str, user_message: str) -> RawGeneration:
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=user_message,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=GenResult,
                    http_options=genai_types.HttpOptions(timeout=self._timeout_ms),
                ),
            )
        except genai_errors.ClientError as exc:
            if exc.code == 429:
                raise AppError(
                    ErrorCode.LLM_RATE_LIMITED,
                    "The model provider is rate-limiting this project right now. "
                    "Wait a moment and retry.",
                    {"provider_status": str(exc.code)},
                ) from exc
            # Every other 4xx - a bad key, a bad model name, a malformed
            # request - has no dedicated code in errors.py, which is frozen
            # this session. LLM_UNAVAILABLE is the closest existing meaning
            # ("the provider could not be used for this request"), even
            # though unlike a real 503, retrying identically will not help.
            # Worth its own code in a later stage; see the stage 3 report.
            raise AppError(
                ErrorCode.LLM_UNAVAILABLE,
                f"The model provider rejected this request ({exc.code}).",
                {"provider_status": str(exc.code)},
            ) from exc
        except genai_errors.ServerError as exc:
            # 504 specifically means the deadline we set via HttpOptions.timeout
            # was hit - measured live: with http_options.timeout below Gemini's
            # own 10s floor, the request 400s immediately (Google refuses a
            # deadline that short); at 10s against real ~20-45s generations,
            # the server aborts in flight and returns 504 DEADLINE_EXCEEDED, not
            # a client-side httpx.TimeoutException. That exception type is only
            # reachable if the connection itself hangs with no response at all -
            # rarer than the deadline simply elapsing, which is what actually
            # happens on this API. Every other 5xx is the routine, not
            # exceptional, unavailability the stage 0 spike measured at one
            # call in ten.
            if exc.code == 504:
                raise AppError(
                    ErrorCode.LLM_TIMEOUT,
                    f"The model did not respond within {settings.llm_timeout_s} seconds.",
                    {"provider_status": str(exc.code)},
                ) from exc
            raise AppError(
                ErrorCode.LLM_UNAVAILABLE,
                "The model provider is temporarily unavailable. Retry shortly.",
                {"provider_status": str(exc.code)},
            ) from exc
        except httpx.TimeoutException as exc:
            # Reachable when the connection itself hangs rather than the
            # server returning a deadline-exceeded response - see the 504
            # branch above for the more common case on this API.
            raise AppError(
                ErrorCode.LLM_TIMEOUT,
                f"The model did not respond within {settings.llm_timeout_s} seconds.",
            ) from exc

        text = response.text
        if not text:
            # Schema-valid-but-empty is not a network failure; it is malformed
            # output by the definition GenResult.model_validate_json would
            # apply anyway, so it reports through the same code.
            raise AppError(
                ErrorCode.LLM_INVALID_OUTPUT,
                "The model returned no text content.",
            )
        usage = response.usage_metadata
        return RawGeneration(
            text=text,
            input_tokens=usage.prompt_token_count if usage else None,
            output_tokens=usage.candidates_token_count if usage else None,
        )


class StubProvider:
    """A canned response for API tests. No network, no cassette lookup.

    `.text` and `.error` are set after construction so one instance can be
    reused across a test's dependency override, configured per test.
    """

    name = "stub"

    def __init__(self, model: str = "stub-model") -> None:
        self.model = model
        self.text: str | None = None
        self.error: AppError | None = None
        self.calls = 0

    def generate(self, *, system_prompt: str, user_message: str) -> RawGeneration:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return RawGeneration(text=self.text or "{}", input_tokens=1, output_tokens=1)


def default_provider() -> LLMProvider:
    """FastAPI dependency in production. Overridden with StubProvider in tests.

    A missing key is refused here, plainly, rather than left to surface as
    whatever google-genai happens to raise when it is asked to authenticate
    with nothing.
    """
    if not settings.google_api_key:
        raise AppError(
            ErrorCode.LLM_UNAVAILABLE,
            "No GOOGLE_API_KEY is configured for this deployment.",
        )
    return GeminiProvider(
        api_key=settings.google_api_key,
        model=settings.llm_model,
        timeout_s=settings.llm_timeout_s,
    )


def generate(profile: ProfileCard, dataset_id: str, provider: LLMProvider) -> GenResult:
    """Run the prompt against `provider`, repairing once on invalid output.

    Every attempt is recorded to the generations table, success or failure -
    that is what gives a later usage report real token and latency numbers
    instead of estimates, and it is why the record happens here rather than
    only at the end.
    """
    system_prompt = prompts.SYSTEM_PROMPT
    base_message = prompts.build_user_message(profile)
    profile_json = profile.model_dump_json()

    message = base_message
    last_error: str | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = time.monotonic()
        try:
            raw = provider.generate(system_prompt=system_prompt, user_message=message)
        except AppError as exc:
            storage.insert_generation(
                dataset_id=dataset_id,
                attempt=attempt,
                state="failed",
                provider=provider.name,
                model=provider.model,
                profile_json=profile_json,
                result_json=None,
                input_tokens=None,
                output_tokens=None,
                latency_ms=int((time.monotonic() - started) * 1000),
                error_code=exc.code.value if hasattr(exc.code, "value") else str(exc.code),
                error_message=exc.message,
            )
            raise
        latency_ms = int((time.monotonic() - started) * 1000)

        try:
            result = GenResult.model_validate_json(raw.text)
        except (ValidationError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            storage.insert_generation(
                dataset_id=dataset_id,
                attempt=attempt,
                state="failed",
                provider=provider.name,
                model=provider.model,
                profile_json=profile_json,
                result_json=None,
                input_tokens=raw.input_tokens,
                output_tokens=raw.output_tokens,
                latency_ms=latency_ms,
                error_code=ErrorCode.LLM_INVALID_OUTPUT.value,
                error_message=last_error,
            )
            message = f"{base_message}\n\n{_REPAIR_NOTE.format(error=last_error)}"
            continue

        storage.insert_generation(
            dataset_id=dataset_id,
            attempt=attempt,
            state="success",
            provider=provider.name,
            model=provider.model,
            profile_json=profile_json,
            result_json=result.model_dump_json(),
            input_tokens=raw.input_tokens,
            output_tokens=raw.output_tokens,
            latency_ms=latency_ms,
            error_code=None,
            error_message=None,
        )
        return result

    raise AppError(
        ErrorCode.LLM_INVALID_OUTPUT,
        f"The model's output did not pass validation after {MAX_ATTEMPTS} attempts. "
        f"Last error: {last_error}",
    )
