"""Dataset routes.

Upload and profile are real as of stage 2. Generate still returns fixtures;
stage 3 replaces it with the Gemini call.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, UploadFile

from app import fixtures, ingest, profiler, storage
from app.errors import AppError, ErrorCode
from app.models import (
    DatasetUploadResponse,
    GenerateRequest,
    GenerateResponse,
    JobState,
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
    """
    filename, frame = await asyncio.to_thread(_load_stored_frame, dataset_id)
    card = await asyncio.to_thread(
        profiler.profile, frame, dataset_id, filename, request.target_column
    )
    return ProfileResponse(state=JobState.COMPLETE, profile=card)


@router.post("/{dataset_id}/generate", response_model=GenerateResponse)
async def generate_pipeline(dataset_id: str, request: GenerateRequest) -> GenerateResponse:
    """Generate a strategy and pipeline code for a profiled dataset.

    The request body carries no profile on purpose. See GenerateRequest.
    Stage 3 puts the Gemini call here and stage 4 the real validator.
    """
    profile = fixtures.profile_card(fixtures.FIXTURE_TARGET)
    return GenerateResponse(
        state=JobState.COMPLETE,
        result=fixtures.gen_result(profile.target_column),
        validation=fixtures.validation_report(),
    )
