"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import datasets_router, health_router
from app.config import settings
from app.models import ErrorDetail, ErrorResponse

API_PREFIX = "/api"


def _envelope(status_code: int, detail: ErrorDetail) -> JSONResponse:
    """Render an error in the one shape every non-2xx response uses."""
    return JSONResponse(status_code=status_code, content=ErrorResponse(error=detail).model_dump())


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic AutoML",
        version=__version__,
        description="Profiles a tabular dataset and generates a modelling pipeline. "
        "Generated code is never executed.",
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
