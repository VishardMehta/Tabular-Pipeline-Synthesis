"""Dataset routes.

Stage 0: every handler returns fixtures. There is no storage, no parsing and no
LLM call behind any of these. The point of the stage is that the response shapes
are final, so stage 1 onward replaces the body of each handler without touching
its signature or the frontend.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app import fixtures
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
    """Accept a CSV and return its column list.

    Stage 1 adds the streaming size check, the C-engine parse, duplicate column
    rejection and SQLite persistence. Stage 0 reads nothing from the upload
    beyond its filename.
    """
    return fixtures.upload_response(file.filename or "")


@router.post("/{dataset_id}/profile", response_model=ProfileResponse)
async def profile_dataset(dataset_id: str, request: ProfileRequest) -> ProfileResponse:
    """Profile a dataset against the chosen target column.

    Stage 2 replaces this with the real profiler. `dataset_id` is accepted and
    ignored here so the frontend can be built against the final URL shape.
    """
    return ProfileResponse(
        state=JobState.COMPLETE,
        profile=fixtures.profile_card(request.target_column),
    )


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
