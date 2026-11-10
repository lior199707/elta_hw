from __future__ import annotations

from dataclasses import dataclass, field

import httpx2
import pytest
from google.genai import errors, types

from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.document_types import Block, BlockKind
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.custom_types.violation_types import CandidateViolation, Severity
from doc_checker.llm.gemini_client import GeminiLlmClient
from doc_checker.llm.llm_errors import (
    LlmBlockedError,
    LlmOverloadedError,
    LlmQuotaExceededError,
    LlmResponseError,
    LlmTimeoutError,
    LlmUnavailableError,
)
from doc_checker.llm.llm_schemas import LlmViolation, LlmViolationReport
from doc_checker.llm.prompt_builder import SYSTEM_INSTRUCTION

pytestmark = pytest.mark.anyio

PRIMARY = "primary-model"
FALLBACK = "fallback-model"
RULES = [CheckRule("R1", "No performance numbers", "Do not disclose numeric performance.")]
CHUNK = Chunk(
    "C1", 1, (Block("B1", 1, BlockKind.PARAGRAPH, "Range is 50 km.", ()),), estimated_tokens=10
)
REPORT = LlmViolationReport(
    violations=[
        LlmViolation(
            rule_id="R1",
            block_id="B1",
            quote="50 km",
            explanation="Reveals range.",
            severity=Severity.HIGH,
        )
    ]
)
EXPECTED_CANDIDATES = (CandidateViolation("R1", "B1", "50 km", "Reveals range.", Severity.HIGH),)


def response(
    text: str = REPORT.model_dump_json(),
    parsed: LlmViolationReport | None = REPORT,
    finish_reason: types.FinishReason = types.FinishReason.STOP,
    block_reason: types.BlockedReason | None = None,
) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=[types.Part(text=text)]),
                finish_reason=finish_reason,
            )
        ],
        prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason=block_reason)
        if block_reason
        else None,
        parsed=parsed,
    )


def api_error(code: int, status: str) -> errors.APIError:
    error_type = errors.ClientError if code < 500 else errors.ServerError
    return error_type(code, {"error": {"code": code, "message": "failure", "status": status}})


QUOTA = api_error(429, "RESOURCE_EXHAUSTED")
OVERLOADED = api_error(503, "UNAVAILABLE")
TIMEOUT = httpx2.ReadTimeout("read timed out")


@dataclass
class FakeModels:
    """Stands in for `genai.Client().aio.models`; outcomes are consumed per model, in order."""

    outcomes: dict[str, list[types.GenerateContentResponse | Exception]]
    calls: list[tuple[str, str, types.GenerateContentConfig]] = field(default_factory=list)

    async def generate_content(
        self, *, model: str, contents: str, config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        self.calls.append((model, contents, config))
        outcome = self.outcomes[model].pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_client(fake: FakeModels) -> GeminiLlmClient:
    return GeminiLlmClient(fake, primary_model=PRIMARY, fallback_model=FALLBACK, temperature=0.0)


async def test_returns_candidates_from_the_primary_model() -> None:
    fake = FakeModels({PRIMARY: [response()]})

    outcome = await make_client(fake).find_violations(RULES, CHUNK)

    assert outcome.candidates == EXPECTED_CANDIDATES
    assert outcome.model_used == PRIMARY
    assert outcome.used_fallback is False
    model, contents, config = fake.calls[0]
    assert model == PRIMARY
    assert "[B1] Range is 50 km." in contents
    assert config.response_schema is LlmViolationReport
    assert config.response_mime_type == "application/json"
    assert config.system_instruction == SYSTEM_INSTRUCTION
    assert config.temperature == 0.0


async def test_falls_back_to_text_when_parsed_is_missing() -> None:
    fake = FakeModels({PRIMARY: [response(parsed=None)]})

    outcome = await make_client(fake).find_violations(RULES, CHUNK)

    assert outcome.candidates == EXPECTED_CANDIDATES


@pytest.mark.parametrize("error", [QUOTA, OVERLOADED, TIMEOUT])
async def test_capacity_error_on_primary_switches_to_fallback(error: Exception) -> None:
    fake = FakeModels({PRIMARY: [error], FALLBACK: [response()]})

    outcome = await make_client(fake).find_violations(RULES, CHUNK)

    assert outcome.model_used == FALLBACK
    assert outcome.used_fallback is True
    assert [call[0] for call in fake.calls] == [PRIMARY, FALLBACK]


async def test_overloaded_on_both_models_raises_overloaded_error() -> None:
    fake = FakeModels({PRIMARY: [OVERLOADED], FALLBACK: [OVERLOADED]})

    with pytest.raises(LlmOverloadedError):
        await make_client(fake).find_violations(RULES, CHUNK)


async def test_quota_error_on_both_models_raises_quota_error() -> None:
    fake = FakeModels({PRIMARY: [QUOTA], FALLBACK: [QUOTA]})

    with pytest.raises(LlmQuotaExceededError):
        await make_client(fake).find_violations(RULES, CHUNK)


@pytest.mark.parametrize("error", [api_error(400, "INVALID_ARGUMENT"), api_error(500, "INTERNAL")])
async def test_other_api_errors_raise_unavailable_without_fallback(error: Exception) -> None:
    fake = FakeModels({PRIMARY: [error], FALLBACK: [response()]})

    with pytest.raises(LlmUnavailableError):
        await make_client(fake).find_violations(RULES, CHUNK)
    assert [call[0] for call in fake.calls] == [PRIMARY]


async def test_blocked_prompt_raises_blocked_error() -> None:
    fake = FakeModels({PRIMARY: [response(parsed=None, block_reason=types.BlockedReason.SAFETY)]})

    with pytest.raises(LlmBlockedError):
        await make_client(fake).find_violations(RULES, CHUNK)


@pytest.mark.parametrize(
    "finish_reason",
    [
        types.FinishReason.SAFETY,
        types.FinishReason.PROHIBITED_CONTENT,
        types.FinishReason.BLOCKLIST,
    ],
)
async def test_safety_finish_reason_raises_blocked_error(finish_reason: types.FinishReason) -> None:
    fake = FakeModels({PRIMARY: [response(parsed=None, finish_reason=finish_reason)]})

    with pytest.raises(LlmBlockedError):
        await make_client(fake).find_violations(RULES, CHUNK)


async def test_truncated_answer_raises_response_error() -> None:
    fake = FakeModels(
        {
            PRIMARY: [
                response(
                    text='{"violations": [',
                    parsed=None,
                    finish_reason=types.FinishReason.MAX_TOKENS,
                )
            ]
        }
    )

    with pytest.raises(LlmResponseError):
        await make_client(fake).find_violations(RULES, CHUNK)


@pytest.mark.parametrize(
    "text",
    [
        "not json at all",
        '{"violations": [{"rule_id": "R1"}]}',
        '{"violations": [{"rule_id": "R1", "block_id": "B1", "quote": "q", '
        '"explanation": "e", "severity": "catastrophic"}]}',
    ],
)
async def test_answer_not_matching_schema_raises_response_error(text: str) -> None:
    fake = FakeModels({PRIMARY: [response(text=text, parsed=None)]})

    with pytest.raises(LlmResponseError):
        await make_client(fake).find_violations(RULES, CHUNK)


async def test_empty_violation_list_is_a_valid_answer() -> None:
    empty = LlmViolationReport(violations=[])
    fake = FakeModels({PRIMARY: [response(text=empty.model_dump_json(), parsed=empty)]})

    outcome = await make_client(fake).find_violations(RULES, CHUNK)

    assert outcome.candidates == ()


async def test_timeout_on_both_models_raises_timeout_error() -> None:
    fake = FakeModels({PRIMARY: [TIMEOUT], FALLBACK: [TIMEOUT]})

    with pytest.raises(LlmTimeoutError):
        await make_client(fake).find_violations(RULES, CHUNK)


async def test_network_error_raises_unavailable_without_fallback() -> None:
    fake = FakeModels({PRIMARY: [httpx2.ConnectError("no route")], FALLBACK: [response()]})

    with pytest.raises(LlmUnavailableError):
        await make_client(fake).find_violations(RULES, CHUNK)
    assert [call[0] for call in fake.calls] == [PRIMARY]
