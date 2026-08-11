"""Liveness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report that the process is up. No dependency checks in MVP-1."""
    return HealthResponse(status="ok", version=__version__)
