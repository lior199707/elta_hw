from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckRule:
    """A rule as presented to the model; `rule_id` is the prompt-local id such as `R1`."""

    rule_id: str
    title: str
    text: str
