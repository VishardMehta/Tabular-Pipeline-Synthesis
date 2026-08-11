"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__, storage
from app.api import datasets_router, health_router
from app.config import settings
from app.errors import AppError
from app.models import ErrorDetail, ErrorResponse

API_PREFIX = "/api"


def _envelope(status_code: int, detail: ErrorDetail) -> JSONResponse:
    """Render an error in the one shape every non-2xx response uses."""
    return JSONResponse(status_code=status_code, content=ErrorResponse(error=detail).model_dump())


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Prepare the database, sweep once, then sweep hourly until shutdown.

    The sweep on boot matters as much as the timer: a process that was down for
    two days would otherwise serve stale datasets until the first hour elapsed.
    """
    storage.init_db()
    await asyncio.to_thread(storage.sweep_expired)
    await asyncio.to_thread(storage.sweep_orphan_files)

    sweeper = asyncio.create_task(storage.sweep_forever())
    try:
        yield
    finally:
        # Without this the task is cancelled at interpreter shutdown and logs a
        # spurious traceback that looks like a real failure during every reload.
        sweeper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sweeper


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic AutoML",
        version=__version__,
        description="Profiles a tabular dataset and generates a modelling pipeline. "
        "Generated code is never executed.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Both handlers exist so that no client ever has to parse two different
    # error shapes. FastAPI's defaults return {"detail": ...}, which would leave
    # the frontend branching on which layer failed.
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_response().model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def _http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        return _envelope(
            exc.status_code,
            ErrorDetail(code="HTTP_ERROR", message=str(exc.detail), retryable=False),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _envelope(
            422,
            ErrorDetail(
                code="INVALID_REQUEST",
                message="The request body did not match the expected schema.",
                retryable=False,
                details={str(e.get("loc", "")): str(e.get("msg", "")) for e in exc.errors()},
            ),
        )

    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(datasets_router, prefix=API_PREFIX)
    return app


app = create_app()
