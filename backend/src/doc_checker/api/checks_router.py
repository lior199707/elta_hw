from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status

from doc_checker.api.api_schemas import (
    CheckResultResponse,
    CheckRunResponse,
    CheckRunSummaryResponse,
)
from doc_checker.api.dependencies import (
    get_check_run_repository,
    get_checker,
    get_config,
    get_rule_repository,
)
from doc_checker.api.error_handlers import FileTooLargeError
from doc_checker.config import AppConfig
from doc_checker.constants import (
    BYTES_PER_MEGABYTE,
    CHECKS_PATH,
    HISTORY_DEFAULT_PAGE_SIZE,
    HISTORY_MAX_PAGE_SIZE,
    RULE_ID_PREFIX,
)
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.repository.check_run_repository import CheckRunRepository
from doc_checker.repository.db_models import CheckRunRecord
from doc_checker.repository.rule_repository import RuleRepository
from doc_checker.services.compliance_checker import ComplianceChecker

router = APIRouter(prefix=CHECKS_PATH, tags=["checks"])

Rules = Annotated[RuleRepository, Depends(get_rule_repository)]
Runs = Annotated[CheckRunRepository, Depends(get_check_run_repository)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_check(
    file: Annotated[UploadFile, File(description="DOCX or TXT document to check")],
    config: Annotated[AppConfig, Depends(get_config)],
    checker: Annotated[ComplianceChecker, Depends(get_checker)],
    rules: Rules,
    runs: Runs,
    rule_ids: Annotated[
        list[int] | None, Form(description="Rules to use; default: all active")
    ] = None,
) -> CheckRunResponse:
    """Run a check and store it in history. Model failures still return 201 with status
    `partial` or `failed`; invalid input returns 4xx before any model call."""
    max_bytes = config.max_upload_mb * BYTES_PER_MEGABYTE
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise FileTooLargeError(f"The file is larger than {config.max_upload_mb} MB.")

    selected = rules.get_many(rule_ids) if rule_ids else rules.list_rules(active_only=True)
    check_rules = [
        CheckRule(rule_id=f"{RULE_ID_PREFIX}{rule.id}", title=rule.title, text=rule.text)
        for rule in selected
    ]
    result = await checker.check(file.filename or "", content, check_rules)

    result_json = CheckResultResponse.model_validate(result).model_dump(mode="json")
    run = runs.add(
        document_name=result.document_name,
        document_sha256=hashlib.sha256(content).hexdigest(),
        document_size_bytes=len(content),
        status=result.status,
        violation_count=len(result.violations),
        models_used=list(result.models_used),
        rules_snapshot=result_json["rules"],
        result=result_json,
        duration_ms=result.duration_ms,
    )
    return _run_response(run)


@router.get("")
def list_checks(
    runs: Runs,
    limit: Annotated[int, Query(ge=1, le=HISTORY_MAX_PAGE_SIZE)] = HISTORY_DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CheckRunSummaryResponse]:
    return [CheckRunSummaryResponse.model_validate(run) for run in runs.list_recent(limit, offset)]


@router.get("/{run_id}")
def get_check(run_id: int, runs: Runs) -> CheckRunResponse:
    return _run_response(runs.get(run_id))


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_check(run_id: int, runs: Runs) -> Response:
    runs.delete(run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _run_response(run: CheckRunRecord) -> CheckRunResponse:
    return CheckRunResponse(
        id=run.id or 0,
        created_at=run.created_at,
        document_sha256=run.document_sha256,
        document_size_bytes=run.document_size_bytes,
        result=CheckResultResponse.model_validate(run.result),
    )
