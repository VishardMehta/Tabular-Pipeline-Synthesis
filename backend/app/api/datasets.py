"""Dataset routes.

Upload, profile and generate are all real as of stage 3.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile

from app import ingest, llm, profiler, storage, validation
from app.errors import AppError, ErrorCode
from app.llm import LLMProvider
from app.models import (
    DatasetDetail,
    DatasetUploadResponse,
    GenerateRequest,
    GenerateResponse,
    GenerationAttempt,
    JobState,
    ProfileCard,
    ProfileRequest,
    ProfileResponse,
    UsageResponse,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetUploadResponse, status_code=201)
async def create_dataset(file: Annotated[UploadFile, File()]) -> DatasetUploadResponse:
    """Accept a CSV, validate it, store it, and return its column list.

    Every refusal path raises AppError with a specific code, rendered by the
    handler in main.py. Parsing runs in a worker thread because pandas holds
    the GIL for the duration and would otherwise stall the event loop for every
    other request in flight.
    """
    raw = await file.read()
    path, frame = await asyncio.to_thread(ingest.ingest, raw)
    return await asyncio.to_thread(
        storage.insert_dataset,
        file.filename or "upload.csv",
        path,
        int(frame.shape[0]),
        int(frame.shape[1]),
        [str(column) for column in frame.columns],
    )


def _load_stored_frame(dataset_id: str) -> tuple[str, pd.DataFrame]:
    """Look up a dataset row and re-parse its file.

    There is no DATASET_NOT_FOUND. An unknown id and an expired id both raise
    DATASET_EXPIRED - see the comment on that code in errors.py for why that
    is a decision, not an oversight. Re-parsing with the C engine rather than
    caching the frame keeps this consistent with the same guarantee ingest.py
    depends on: whatever reads a file, reads it the same way every time.
    """
    row = storage.get_dataset(dataset_id)
    if row is None:
        raise AppError(
            ErrorCode.DATASET_EXPIRED,
            "This dataset is no longer available. Upload the file again.",
            {"dataset_id": dataset_id},
        )
    frame = ingest.parse_csv(Path(row["stored_path"]))
    return row["filename"], frame


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset_detail(dataset_id: str) -> DatasetDetail:
    """Everything on record for one dataset, profile included when it exists.

    The recovery path. Upload, profile and generate are all POSTs, so before
    this existed a browser refresh threw away a session whose dataset and
    profile were still in SQLite and still inside their TTL - and re-profiling
    is cheap but re-generating costs one of twenty daily model requests.

    A dataset with no profile yet returns 200 with `profile: null`. That is a
    normal point in the flow, not a failure, so unlike /generate it is not
    folded into DATASET_EXPIRED.
    """
    row = await asyncio.to_thread(storage.get_dataset, dataset_id)
    if row is None:
        raise AppError(
            ErrorCode.DATASET_EXPIRED,
            "This dataset is no longer available. Upload the file again.",
            {"dataset_id": dataset_id},
        )
    return DatasetDetail(
        dataset_id=row["id"],
        filename=row["filename"],
        n_rows=row["n_rows"],
        n_columns=row["n_columns"],
        columns=json.loads(row["columns_json"]),
        created_at=row["created_at"],
        state=JobState(row["state"]),
        task_was_overridden=bool(row["task_overridden"]),
        profile=(
            ProfileCard.model_validate_json(row["profile_json"])
            if row["profile_json"] is not None
            else None
        ),
    )


@router.get("/{dataset_id}/usage", response_model=UsageResponse)
async def get_dataset_usage(dataset_id: str) -> UsageResponse:
    """Every recorded provider attempt for this dataset.

    The generations table has been written since stage 3 and read by nothing
    but tests, which made it write-only data. Tokens and latency here are
    measured facts about the HTTP calls, not quality claims about the pipeline -
    no score for the generated code appears here or anywhere else.

    Attempts include failures and the repair round, because "this dataset cost
    three attempts" is the number that matters against a 20/day quota.
    """
    row = await asyncio.to_thread(storage.get_dataset, dataset_id)
    if row is None:
        raise AppError(
            ErrorCode.DATASET_EXPIRED,
            "This dataset is no longer available. Upload the file again.",
            {"dataset_id": dataset_id},
        )
    rows = await asyncio.to_thread(storage.get_generations, dataset_id)
    attempts = [
        GenerationAttempt(
            attempt=record["attempt"],
            state=record["state"],
            provider=record["provider"],
            model=record["model"],
            input_tokens=record["input_tokens"],
            output_tokens=record["output_tokens"],
            latency_ms=record["latency_ms"],
            error_code=record["error_code"],
            error_message=record["error_message"],
            created_at=record["created_at"],
        )
        for record in rows
    ]
    return UsageResponse(
        dataset_id=dataset_id,
        attempts=attempts,
        total_attempts=len(attempts),
        total_input_tokens=sum(a.input_tokens or 0 for a in attempts),
        total_output_tokens=sum(a.output_tokens or 0 for a in attempts),
    )


@router.post("/{dataset_id}/profile", response_model=ProfileResponse)
async def profile_dataset(dataset_id: str, request: ProfileRequest) -> ProfileResponse:
    """Profile a dataset against the chosen target column.

    TARGET_NOT_FOUND, TARGET_ALL_NULL, TARGET_SINGLE_VALUE and
    TARGET_TYPE_UNSUPPORTED all originate inside profiler.profile and are
    rendered by the same AppError handler as every ingest rejection.

    The card is persisted here, not just returned, because /generate has no
    ProfileCard of its own to work from - GenerateRequest is deliberately
    empty, see its docstring in models.py.
    """
    filename, frame = await asyncio.to_thread(_load_stored_frame, dataset_id)
    card = await asyncio.to_thread(
        profiler.profile,
        frame,
        dataset_id,
        filename,
        request.target_column,
        request.problem_type_override,
    )
    await asyncio.to_thread(
        storage.save_profile,
        dataset_id,
        card.model_dump_json(),
        request.problem_type_override is not None,
    )
    return ProfileResponse(state=JobState.COMPLETE, profile=card)


def _load_stored_profile(dataset_id: str) -> ProfileCard:
    """Look up the ProfileCard /profile left behind for this dataset.

    Folded into DATASET_EXPIRED rather than a new code: errors.py is frozen
    this session, and from the caller's perspective an id with no profile on
    record is not in a state /generate can act on, same as an id that never
    existed or has aged out. See the comment on DATASET_EXPIRED in errors.py
    for the precedent - this is the same tradeoff, one more time.
    """
    row = storage.get_dataset(dataset_id)
    if row is None or row["profile_json"] is None:
        raise AppError(
            ErrorCode.DATASET_EXPIRED,
            "This dataset has not been profiled yet, or is no longer available. "
            "Profile it again before generating.",
            {"dataset_id": dataset_id},
        )
    return ProfileCard.model_validate_json(row["profile_json"])


# One in-flight generation per dataset.
#
# Not a nicety. The free tier allows 20 model requests per day per project per
# model, so a double-clicked button costs 10% of a day's budget for a result
# the user will only look at once. There is no jobs table to hang a database
# constraint on while /generate stays synchronous, so this is an in-process
# guard: correct for the single-worker deployment this app actually runs as,
# and honestly limited for anything beyond it.
#
# asyncio.Lock rather than threading.Lock: the contended section is the await
# of the generation itself, so it has to be held across an await point.
_IN_FLIGHT: dict[str, asyncio.Lock] = {}


@contextlib.asynccontextmanager
async def _single_generation(dataset_id: str):
    """Refuse a second concurrent generation for one dataset.

    Refuses rather than queues. Queuing would spend the second call's quota to
    return an answer nobody asked for twice, and the caller would wait the full
    round trip to learn that.
    """
    lock = _IN_FLIGHT.setdefault(dataset_id, asyncio.Lock())
    if lock.locked():
        raise AppError(
            ErrorCode.LLM_RATE_LIMITED,
            "A pipeline is already being generated for this dataset. Wait for it "
            "to finish before starting another.",
            {"dataset_id": dataset_id, "reason": "already_in_flight"},
        )
    async with lock:
        try:
            yield
        finally:
            # Only drop the entry when nobody else is waiting on it, or a
            # long-lived process accumulates one lock per dataset forever.
            if not lock.locked():
                _IN_FLIGHT.pop(dataset_id, None)


def _validate_exclusions(requested: list[str], profile: ProfileCard) -> list[str]:
    """Check an exclusion list against the profile the server itself computed.

    Two refusals, both TARGET_* or ingest-family codes rather than new ones,
    because errors.py is treated as frozen and neither case needs a code of its
    own to be actionable:

    - A name that is not a column in this dataset is almost always a typo or a
      stale client, and silently ignoring it would mean the user believes a
      column was dropped when it was not. TARGET_NOT_FOUND already means
      "you named a column that does not exist here".
    - Excluding the target would leave nothing to predict. TARGET_SINGLE_VALUE
      is the nearest existing meaning: the target is unusable as given.

    Returns the list in profile column order so the prompt text is stable
    regardless of the order the client sent.
    """
    if not requested:
        return []

    known = {column.name for column in profile.columns}
    unknown = sorted(set(requested) - known)
    if unknown:
        raise AppError(
            ErrorCode.TARGET_NOT_FOUND,
            "These columns are not in this dataset: " + ", ".join(unknown),
            {"unknown_columns": ", ".join(unknown)},
        )
    if profile.target_column in requested:
        raise AppError(
            ErrorCode.TARGET_SINGLE_VALUE,
            f"'{profile.target_column}' is the target column and cannot be excluded. "
            "Profile the dataset against a different target instead.",
            {"target_column": profile.target_column},
        )

    requested_set = set(requested)
    return [column.name for column in profile.columns if column.name in requested_set]


@router.post("/{dataset_id}/generate", response_model=GenerateResponse)
async def generate_pipeline(
    dataset_id: str,
    request: GenerateRequest,
    provider: Annotated[LLMProvider, Depends(llm.default_provider)],
) -> GenerateResponse:
    """Generate a strategy and pipeline code for a profiled dataset, then
    validate it statically.

    The request body carries no profile on purpose. See GenerateRequest. The
    profile read here is the one /profile persisted, never one the caller
    could supply.

    The report is returned alongside the result regardless of severity - a
    FAIL does not suppress the code. The user is shown what was generated and
    why it failed, not left to wonder what got hidden. VALIDATION_FAILED in
    errors.py is not raised here: it is retryable=false, meant for phase 2's
    repair loop, and a ValidationReport rendered as a checklist is the
    correct response to output that parsed but did not pass, not an error.
    """
    profile = await asyncio.to_thread(_load_stored_profile, dataset_id)
    excluded = _validate_exclusions(request.excluded_columns, profile)
    # Both refusals above happen before the guard, so a malformed request never
    # blocks a well-formed one and never spends a model call.
    async with _single_generation(dataset_id):
        result = await asyncio.to_thread(llm.generate, profile, dataset_id, provider, excluded)
        report = await asyncio.to_thread(validation.validate, result, profile, excluded)
    return GenerateResponse(state=JobState.COMPLETE, result=result, validation=report)
