"""Every way a request can fail, in one place.

Not prompt surface. Nothing in this file is ever sent to a model, so docstrings
here are for humans like the comments are.

Three rules hold this together:

  Every code carries its HTTP status and its retryability as data, not as a
  decision made at the raise site. Two handlers raising the same code cannot
  disagree about whether the client may retry.

  `retryable` means precisely one thing: repeating the identical request may
  succeed without the user changing anything. It is not a severity and it is
  not a hint. The frontend renders a retry button directly from it, so a wrong
  value produces either a dead button or a hidden recovery path.

  Messages are written for a person who will act on them. They name the
  offending thing. "Duplicate column names: id, id" beats "invalid CSV".
"""

from __future__ import annotations

from enum import StrEnum
from typing import NamedTuple

from app.models import ErrorDetail, ErrorResponse


class ErrorCode(StrEnum):
    """Stable identifiers. The frontend branches on these, so never rename."""

    # Ingest: the upload itself
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNPARSEABLE_CSV = "UNPARSEABLE_CSV"
    DATASET_TOO_LARGE_IN_MEMORY = "DATASET_TOO_LARGE_IN_MEMORY"

    # Ingest: the shape of what was parsed
    EMPTY_DATASET = "EMPTY_DATASET"
    HEADER_ONLY = "HEADER_ONLY"
    SINGLE_COLUMN = "SINGLE_COLUMN"
    TOO_MANY_COLUMNS = "TOO_MANY_COLUMNS"
    DUPLICATE_COLUMNS = "DUPLICATE_COLUMNS"

    # Target selection
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    TARGET_ALL_NULL = "TARGET_ALL_NULL"
    TARGET_SINGLE_VALUE = "TARGET_SINGLE_VALUE"
    # Added in stage 2. The dtype ladder classifies a target as TEXT, DATETIME
    # or UNKNOWN for columns this system has no way to model: free text, a raw
    # timestamp, or a column with no non-null values that survived selection.
    # There is no ProblemType member for any of those, and fabricating a
    # confidence-weighted guess would be exactly the kind of invented number
    # this project exists to avoid. Refusing cleanly is the honest option.
    TARGET_TYPE_UNSUPPORTED = "TARGET_TYPE_UNSUPPORTED"

    # Lifecycle
    DATASET_EXPIRED = "DATASET_EXPIRED"

    # Generation. Stage 3 raises these; the enum is written once, here.
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_INVALID_OUTPUT = "LLM_INVALID_OUTPUT"

    # Validation. Stage 4.
    # Declared but deliberately never raised today. A failing ValidationReport
    # ships alongside the code, never instead of it - the reader is shown what
    # failed and decides. This code is reserved for a future repair loop, where
    # the server retries generation against the failing checks and gives up.
    # Until that exists, `grep VALIDATION_FAILED app/` finding no `raise` is the
    # correct result, not a missing implementation.
    VALIDATION_FAILED = "VALIDATION_FAILED"


class ErrorSpec(NamedTuple):
    """How one code is presented to the client."""

    status: int
    retryable: bool


# Every code appears here exactly once. A test asserts the mapping is total, so
# adding a code without deciding its status and retryability fails the suite
# rather than defaulting to something plausible.
#
# On the retryable column: everything an ingest check rejects is a property of
# the file the user chose, so repeating the request reproduces the failure
# exactly. Those are all False, and the remedy is a different file, which the
# message has to say. Only the provider-side failures are True, because those
# are the only ones where the same bytes may succeed on a second attempt.
ERROR_SPECS: dict[ErrorCode, ErrorSpec] = {
    # 413 rather than 422: the request is well formed, it is the size that is
    # refused, and 413 is what a proxy in front of this would return anyway.
    ErrorCode.FILE_TOO_LARGE: ErrorSpec(413, False),
    ErrorCode.DATASET_TOO_LARGE_IN_MEMORY: ErrorSpec(413, False),
    ErrorCode.UNPARSEABLE_CSV: ErrorSpec(422, False),
    ErrorCode.EMPTY_DATASET: ErrorSpec(422, False),
    ErrorCode.HEADER_ONLY: ErrorSpec(422, False),
    ErrorCode.SINGLE_COLUMN: ErrorSpec(422, False),
    ErrorCode.TOO_MANY_COLUMNS: ErrorSpec(422, False),
    ErrorCode.DUPLICATE_COLUMNS: ErrorSpec(422, False),
    ErrorCode.TARGET_NOT_FOUND: ErrorSpec(422, False),
    ErrorCode.TARGET_ALL_NULL: ErrorSpec(422, False),
    ErrorCode.TARGET_SINGLE_VALUE: ErrorSpec(422, False),
    ErrorCode.TARGET_TYPE_UNSUPPORTED: ErrorSpec(422, False),
    # 410 rather than 404. The dataset existed and was deleted on TTL, and
    # saying so tells the user to re-upload rather than to check the URL.
    #
    # There is deliberately no DATASET_NOT_FOUND. An unknown id and an expired
    # id return this same code, which means a typo is told the dataset expired.
    # That small inaccuracy is the price of not answering the question "did this
    # UUID ever exist", which is an enumeration oracle for anyone who wants one.
    # The remedy is identical either way: upload the file again. This is a
    # decision, not an oversight.
    ErrorCode.DATASET_EXPIRED: ErrorSpec(410, False),
    # 503 from the provider was a routine failure in the stage 0 spike, not an
    # edge case: one call in ten. Retryable, and distinct from a quota refusal
    # because the remedies differ - wait seconds versus wait until tomorrow.
    ErrorCode.LLM_UNAVAILABLE: ErrorSpec(503, True),
    ErrorCode.LLM_RATE_LIMITED: ErrorSpec(429, True),
    ErrorCode.LLM_TIMEOUT: ErrorSpec(504, True),
    # 502: the upstream answered with something this service cannot use.
    # Retryable because generation is not deterministic, so the identical
    # prompt can well produce parseable output on a second attempt.
    ErrorCode.LLM_INVALID_OUTPUT: ErrorSpec(502, True),
    # NOT retryable, unlike LLM_INVALID_OUTPUT, and the distinction is the point.
    #
    # LLM_INVALID_OUTPUT means the model returned something unparseable, so a
    # second attempt is a genuinely fresh roll. VALIDATION_FAILED means it
    # returned well formed output that failed a check: a hallucinated column, a
    # forbidden import, a metric inconsistent with the profile. Retrying that is
    # a blind reroll against an unchanged prompt, so the expected outcome is the
    # same failure, paid for out of a free-tier quota.
    #
    # The correct response is repair, not retry, and repair is the phase-2
    # self-correction loop. Marking this retryable would paper over the exact
    # gap that loop exists to fill. When phase 2 lands, this code triggers a
    # REPAIRING state rather than a user-facing button.
    #
    # Not the ordinary path for a failing check: a ValidationReport with
    # passed=False is a 200 that renders as a checklist. This code is for
    # errors severe enough that returning the code at all would mislead.
    ErrorCode.VALIDATION_FAILED: ErrorSpec(422, False),
}


class AppError(Exception):
    """Raised anywhere in the app, rendered by one handler in main.py.

    Carrying the code rather than the HTTP status means call sites never think
    about transport, and there is exactly one place where a code becomes a
    response.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    @property
    def spec(self) -> ErrorSpec:
        return ERROR_SPECS[self.code]

    @property
    def status_code(self) -> int:
        return self.spec.status

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(
            error=ErrorDetail(
                code=self.code.value,
                message=self.message,
                retryable=self.spec.retryable,
                details=self.details,
            )
        )
