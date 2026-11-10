from __future__ import annotations

from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.document_types import Block, BlockKind
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.llm.prompt_builder import SYSTEM_INSTRUCTION, build_user_prompt

RULES = [
    CheckRule("R1", "No performance numbers", "Do not disclose numeric performance."),
    CheckRule("R2", "No names", "Do not mention personnel names."),
]
CHUNK = Chunk(
    chunk_id="C1",
    index=1,
    blocks=(
        Block("B1", 1, BlockKind.HEADING, "Specs", ("Specs",)),
        Block("B2", 2, BlockKind.PARAGRAPH, "Range is 50 km.", ("Specs",)),
    ),
    estimated_tokens=20,
)


def test_rules_section_lists_every_rule_with_its_id() -> None:
    prompt = build_user_prompt(RULES, CHUNK)

    rules_section = prompt.split("<rules>")[1].split("</rules>")[0]
    assert "R1 [No performance numbers]: Do not disclose numeric performance." in rules_section
    assert "R2 [No names]: Do not mention personnel names." in rules_section


def test_document_section_holds_rendered_blocks_in_order() -> None:
    prompt = build_user_prompt(RULES, CHUNK)

    document_section = prompt.split("<document>")[1].split("</document>")[0]
    assert document_section.strip().splitlines() == [
        "[B1] (Specs) Specs",
        "[B2] (Specs) Range is 50 km.",
    ]


def test_rules_come_before_the_document() -> None:
    prompt = build_user_prompt(RULES, CHUNK)

    assert prompt.index("<rules>") < prompt.index("<document>")


def test_system_instruction_demands_verbatim_quotes_and_treats_document_as_untrusted() -> None:
    lowered = SYSTEM_INSTRUCTION.lower()

    assert "exact" in lowered
    assert "untrusted" in lowered
    assert "empty list" in lowered
