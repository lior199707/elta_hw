from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from doc_checker.custom_types.violation_types import Severity


class LlmViolation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rule_id: str = Field(description="Id of the violated rule, for example R1.")
    block_id: str = Field(description="Id of the block containing the passage, for example B12.")
    quote: str = Field(description="Shortest exact passage, copied character for character.")
    explanation: str = Field(description="One or two sentences on why it violates the rule.")
    severity: Severity


class LlmViolationReport(BaseModel):
    """Response schema enforced on the model through structured output."""

    model_config = ConfigDict(extra="ignore")

    violations: list[LlmViolation]
