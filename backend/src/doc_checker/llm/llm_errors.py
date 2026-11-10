from __future__ import annotations


class LlmError(Exception):
    """Base for all failures talking to the language model."""


class LlmQuotaExceededError(LlmError):
    """The model's request quota is exhausted (HTTP 429)."""


class LlmBlockedError(LlmError):
    """The model refused the request or its answer was blocked by safety filters."""


class LlmResponseError(LlmError):
    """The model answered, but the answer is truncated or does not match the schema."""


class LlmUnavailableError(LlmError):
    """The API call failed for a reason other than quota (network, 4xx, 5xx after retries)."""


class LlmOverloadedError(LlmUnavailableError):
    """The model is temporarily over capacity (HTTP 503) even after the SDK's retries."""


class LlmTimeoutError(LlmUnavailableError):
    """The model did not answer within the request timeout."""
