"""What the model receives, verified with a spy LLM and a fake SDK (no network, no quota)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from google.genai import types

from doc_checker.chunking.block_chunker import build_chunks
from doc_checker.chunking.block_rendering import render_block_line
from doc_checker.config import AppConfig
from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.llm_types import LlmCheckOutcome
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.custom_types.violation_types import CandidateViolation, Severity
from doc_checker.extraction.document_extraction import extract_document
from doc_checker.llm.gemini_client import GeminiLlmClient
from doc_checker.llm.llm_schemas import LlmViolationReport
from doc_checker.llm.prompt_builder import SYSTEM_INSTRUCTION, build_user_prompt
from doc_checker.repository.default_rules import DEFAULT_RULES
from doc_checker.services.compliance_checker import ComplianceChecker
from tests.fakes import FakeLlm
from tests.fixtures.sample_documents import HARD, SAMPLE_DOCUMENTS, RuleKey, SampleDocument

pytestmark = pytest.mark.anyio

RULE_ID_BY_KEY = {RuleKey.PERFORMANCE: "R1", RuleKey.NAMES: "R2", RuleKey.LOCATIONS: "R3"}
RULES = [
    CheckRule(f"R{position}", title, text)
    for position, (title, text) in enumerate(DEFAULT_RULES, start=1)
]
DEFAULT_BUDGET = AppConfig.model_fields["chunk_token_budget"].default
SMALL_BUDGET = 2_000


def reports_planted(sample: SampleDocument) -> FakeLlm:
    """A model that finds exactly the planted violations visible in each chunk."""

    def respond(chunk: Chunk) -> LlmCheckOutcome:
        found = [
            CandidateViolation(
                RULE_ID_BY_KEY[planted.rule],
                block.block_id,
                planted.quote_contains,
                "planted",
                Severity.HIGH,
            )
            for block in chunk.blocks
            for planted in sample.planted
            if planted.quote_contains in block.text
        ]
        return LlmCheckOutcome(candidates=tuple(found), model_used="spy")

    return FakeLlm(respond)


@pytest.mark.parametrize("sample", SAMPLE_DOCUMENTS, ids=lambda s: s.level)
@pytest.mark.parametrize("budget", [SMALL_BUDGET, DEFAULT_BUDGET])
async def test_every_block_and_every_rule_is_sent(sample: SampleDocument, budget: int) -> None:
    llm = reports_planted(sample)
    checker = ComplianceChecker(llm, token_budget=budget, overlap_blocks=2, max_concurrency=2)

    await checker.check(sample.filename, sample.build(), RULES)

    sent_ids = {block.block_id for _, chunk in llm.calls for block in chunk.blocks}
    all_ids = {b.block_id for b in extract_document(sample.filename, sample.build()).blocks}
    assert sent_ids == all_ids
    assert all(list(rules) == RULES for rules, _ in llm.calls)


@pytest.mark.parametrize("sample", SAMPLE_DOCUMENTS, ids=lambda s: s.level)
@pytest.mark.parametrize("budget", [SMALL_BUDGET, DEFAULT_BUDGET])
async def test_planted_findings_survive_the_whole_pipeline_exactly_once(
    sample: SampleDocument, budget: int
) -> None:
    checker = ComplianceChecker(
        reports_planted(sample), token_budget=budget, overlap_blocks=2, max_concurrency=2
    )

    result = await checker.check(sample.filename, sample.build(), RULES)

    reported = sorted((v.rule_id, v.quote) for v in result.violations)
    expected = sorted((RULE_ID_BY_KEY[p.rule], p.quote_contains) for p in sample.planted)
    assert reported == expected, "missing, extra or duplicated (overlap) findings"
    assert result.dropped_count == 0


def test_prompt_holds_all_rules_then_exactly_the_chunk_lines_in_order() -> None:
    blocks = extract_document(HARD.filename, HARD.build()).blocks
    chunks = build_chunks(blocks, SMALL_BUDGET, 2)

    for chunk in chunks:
        prompt = build_user_prompt(RULES, chunk)
        rules_section = prompt.split("<rules>")[1].split("</rules>")[0]
        document_section = prompt.split("<document>")[1].split("</document>")[0]
        for rule in RULES:
            assert f"{rule.rule_id} [{rule.title}]: {rule.text}" in rules_section
        assert document_section.strip().splitlines() == [
            render_block_line(block) for block in chunk.blocks
        ]


@dataclass
class CapturingModels:
    calls: list[tuple[str, str, types.GenerateContentConfig]] = field(default_factory=list)

    async def generate_content(
        self, *, model: str, contents: str, config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        self.calls.append((model, contents, config))
        empty = LlmViolationReport(violations=[])
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text=empty.model_dump_json())]
                    ),
                    finish_reason=types.FinishReason.STOP,
                )
            ],
            parsed=empty,
        )


async def test_gemini_request_carries_prompt_schema_and_settings() -> None:
    blocks = extract_document(HARD.filename, HARD.build()).blocks
    chunk = build_chunks(blocks, SMALL_BUDGET, 2)[3]
    models = CapturingModels()
    client = GeminiLlmClient(models, primary_model="m", fallback_model="f", temperature=0.0)

    await client.find_violations(RULES, chunk)

    model, contents, config = models.calls[0]
    assert model == "m"
    assert contents == build_user_prompt(RULES, chunk)
    assert config.system_instruction == SYSTEM_INSTRUCTION
    assert config.response_mime_type == "application/json"
    assert config.response_schema is LlmViolationReport
    assert config.temperature == 0.0
