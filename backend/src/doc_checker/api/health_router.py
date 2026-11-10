from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from doc_checker.api.dependencies import get_config
from doc_checker.config import AppConfig
from doc_checker.constants import HEALTH_PATH, HEALTH_STATUS_OK

router = APIRouter()


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    llm_model: str
    llm_fallback_model: str


@router.get(HEALTH_PATH)
def get_health(config: Annotated[AppConfig, Depends(get_config)]) -> HealthResponse:
    return HealthResponse(
        status=HEALTH_STATUS_OK,
        llm_model=config.llm_model,
        llm_fallback_model=config.llm_fallback_model,
    )
