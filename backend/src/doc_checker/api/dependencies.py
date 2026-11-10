from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from doc_checker.config import AppConfig
from doc_checker.repository.check_run_repository import CheckRunRepository
from doc_checker.repository.rule_repository import RuleRepository
from doc_checker.services.compliance_checker import ComplianceChecker


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_checker(request: Request) -> ComplianceChecker:
    return request.app.state.checker


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session


def get_rule_repository(session: Annotated[Session, Depends(get_session)]) -> RuleRepository:
    return RuleRepository(session)


def get_check_run_repository(
    session: Annotated[Session, Depends(get_session)],
) -> CheckRunRepository:
    return CheckRunRepository(session)
