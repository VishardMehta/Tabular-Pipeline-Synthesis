"""Dataset routes.

Upload, profile and generate are all real as of stage 3.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile

from app import ingest, llm, profiler, storage, validation
from app.errors import AppError, ErrorCode
from app.llm import LLMProvider
from app.models import (
    DatasetUploadResponse,
    GenerateRequest,
    GenerateResponse,
    JobState,
    ProfileCard,
    ProfileRequest,
    ProfileResponse,
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
        profiler.profile, frame, dataset_id, filename, request.target_column
    )
    await asyncio.to_thread(storage.save_profile, dataset_id, card.model_dump_json())
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
    result = await asyncio.to_thread(llm.generate, profile, dataset_id, provider)
    report = await asyncio.to_thread(validation.validate, result, profile)
    return GenerateResponse(state=JobState.COMPLETE, result=result, validation=report)
