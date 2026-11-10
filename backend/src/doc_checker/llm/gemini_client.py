from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Protocol

import httpx2
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from doc_checker.config import AppConfig
from doc_checker.constants import (
    HTTP_STATUS_SERVICE_UNAVAILABLE,
    HTTP_STATUS_TOO_MANY_REQUESTS,
    LLM_HTTP_RETRY_ATTEMPTS,
    LLM_REQUEST_TIMEOUT_MS,
    LLM_RESPONSE_MIME_TYPE,
    LLM_RETRYABLE_HTTP_STATUS_CODES,
)
from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.llm_types import LlmCheckOutcome
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.custom_types.violation_types import CandidateViolation
from doc_checker.llm.llm_errors import (
    LlmBlockedError,
    LlmOverloadedError,
    LlmQuotaExceededError,
    LlmResponseError,
    LlmTimeoutError,
    LlmUnavailableError,
)
from doc_checker.llm.llm_schemas import LlmViolationReport
from doc_checker.llm.prompt_builder import SYSTEM_INSTRUCTION, build_user_prompt

logger = logging.getLogger(__name__)

_BLOCKING_FINISH_REASONS = frozenset(
    {
        types.FinishReason.SAFETY,
        types.FinishReason.PROHIBITED_CONTENT,
        types.FinishReason.BLOCKLIST,
        types.FinishReason.SPII,
        types.FinishReason.RECITATION,
    }
)


class GenerateContentApi(Protocol):
    """The slice of `genai.Client().aio.models` this client uses (lets tests pass a fake)."""

    async def generate_content(
        self, *, model: str, contents: str, config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse: ...


def create_gemini_sdk_client(config: AppConfig) -> genai.Client:
    """Create the SDK client once at startup, with retries on 5xx (never on 429)."""
    return genai.Client(
        api_key=config.gemini_api_key.get_secret_value(),
        http_options=types.HttpOptions(
            timeout=LLM_REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(
                attempts=LLM_HTTP_RETRY_ATTEMPTS,
                http_status_codes=list(LLM_RETRYABLE_HTTP_STATUS_CODES),
            ),
        ),
    )


class GeminiLlmClient:
    def __init__(
        self,
        models: GenerateContentApi,
        primary_model: str,
        fallback_model: str,
        temperature: float,
    ) -> None:
        self._models = models
        self._primary_model = primary_model
        self._fallback_model = fallback_model
        self._generate_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=temperature,
            response_mime_type=LLM_RESPONSE_MIME_TYPE,
            response_schema=LlmViolationReport,
        )

    async def find_violations(self, rules: Sequence[CheckRule], chunk: Chunk) -> LlmCheckOutcome:
        """Call the primary model; on a capacity error (429, 503, timeout) use the fallback.

        Raises LlmQuotaExceededError, LlmOverloadedError, LlmTimeoutError (fallback also out of
        capacity), LlmBlockedError, LlmResponseError, or LlmUnavailableError.
        """
        prompt = build_user_prompt(rules, chunk)
        try:
            return await self._generate(self._primary_model, prompt, chunk, used_fallback=False)
        except (LlmQuotaExceededError, LlmOverloadedError, LlmTimeoutError) as exc:
            logger.warning(
                "primary model out of capacity, switching to fallback",
                extra={
                    "chunk_id": chunk.chunk_id,
                    "error_type": type(exc).__name__,
                    "primary_model": self._primary_model,
                    "fallback_model": self._fallback_model,
                },
            )
            return await self._generate(self._fallback_model, prompt, chunk, used_fallback=True)

    async def _generate(
        self, model: str, prompt: str, chunk: Chunk, used_fallback: bool
    ) -> LlmCheckOutcome:
        log_context = {"chunk_id": chunk.chunk_id, "llm_model": model}
        try:
            response = await self._models.generate_content(
                model=model, contents=prompt, config=self._generate_config
            )
        except errors.APIError as exc:
            if exc.code == HTTP_STATUS_TOO_MANY_REQUESTS:
                raise LlmQuotaExceededError(f"Quota exhausted for model {model!r}.") from exc
            if exc.code == HTTP_STATUS_SERVICE_UNAVAILABLE:
                raise LlmOverloadedError(
                    f"Model {model!r} is overloaded, try again later."
                ) from exc
            logger.error(
                "llm request failed",
                extra={**log_context, "status_code": exc.code, "api_status": exc.status},
            )
            raise LlmUnavailableError(
                f"Model {model!r} request failed with HTTP {exc.code} ({exc.status})."
            ) from exc
        except httpx2.TimeoutException as exc:
            logger.warning("llm request timed out", extra=log_context)
            raise LlmTimeoutError(f"Model {model!r} did not answer in time.") from exc
        except httpx2.TransportError as exc:
            logger.error(
                "llm request transport failure",
                extra={**log_context, "error_type": type(exc).__name__},
            )
            raise LlmUnavailableError(f"Could not reach model {model!r}.") from exc

        report = _parse_report(response, model)
        usage = response.usage_metadata
        logger.info(
            "llm chunk checked",
            extra={
                **log_context,
                "candidate_count": len(report.violations),
                "prompt_tokens": usage.prompt_token_count if usage else None,
                "output_tokens": usage.candidates_token_count if usage else None,
            },
        )
        return LlmCheckOutcome(
            candidates=_to_candidates(report), model_used=model, used_fallback=used_fallback
        )


def _parse_report(response: types.GenerateContentResponse, model: str) -> LlmViolationReport:
    feedback = response.prompt_feedback
    if feedback is not None and feedback.block_reason is not None:
        raise LlmBlockedError(f"Model {model!r} blocked the request ({feedback.block_reason}).")

    if not response.candidates:
        raise LlmResponseError(f"Model {model!r} returned no answer.")
    finish_reason = response.candidates[0].finish_reason
    if finish_reason in _BLOCKING_FINISH_REASONS:
        raise LlmBlockedError(f"Model {model!r} answer was blocked ({finish_reason}).")
    if finish_reason == types.FinishReason.MAX_TOKENS:
        raise LlmResponseError(f"Model {model!r} answer was truncated (output token limit).")

    if isinstance(response.parsed, LlmViolationReport):
        return response.parsed
    try:
        return LlmViolationReport.model_validate_json(response.text or "")
    except ValidationError as exc:
        raise LlmResponseError(
            f"Model {model!r} answer does not match the violation schema."
        ) from exc


def _to_candidates(report: LlmViolationReport) -> tuple[CandidateViolation, ...]:
    return tuple(
        CandidateViolation(
            rule_id=violation.rule_id,
            block_id=violation.block_id,
            quote=violation.quote,
            explanation=violation.explanation,
            severity=violation.severity,
        )
        for violation in report.violations
    )
