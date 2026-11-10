from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from doc_checker.api.api_schemas import RuleCreateRequest, RuleResponse, RuleUpdateRequest
from doc_checker.api.dependencies import get_rule_repository
from doc_checker.constants import RULES_PATH
from doc_checker.repository.rule_repository import RuleRepository

router = APIRouter(prefix=RULES_PATH, tags=["rules"])

Rules = Annotated[RuleRepository, Depends(get_rule_repository)]


@router.get("")
def list_rules(rules: Rules, active: bool = False) -> list[RuleResponse]:
    return [RuleResponse.model_validate(rule) for rule in rules.list_rules(active_only=active)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleCreateRequest, rules: Rules) -> RuleResponse:
    return RuleResponse.model_validate(rules.create(payload.title, payload.text, payload.is_active))


@router.patch("/{rule_id}")
def update_rule(rule_id: int, payload: RuleUpdateRequest, rules: Rules) -> RuleResponse:
    updated = rules.update(
        rule_id, title=payload.title, text=payload.text, is_active=payload.is_active
    )
    return RuleResponse.model_validate(updated)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, rules: Rules) -> Response:
    rules.delete(rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
