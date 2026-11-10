from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import Engine, StaticPool, make_url
from sqlmodel import Session, SQLModel, create_engine, select

from doc_checker.constants import SQLITE_MEMORY_DATABASE
from doc_checker.repository import db_models  # noqa: F401  (registers the tables on SQLModel)
from doc_checker.repository.db_models import RuleRecord
from doc_checker.repository.default_rules import DEFAULT_RULES

logger = logging.getLogger(__name__)

_SQLITE_DRIVER_PREFIX = "sqlite"


def create_db_engine(database_url: str) -> Engine:
    """Create the engine; for a SQLite file, create its parent directory if it is missing.

    An in-memory SQLite URL gets a single shared connection so every session sees the same data.
    """
    url = make_url(database_url)
    if not url.drivername.startswith(_SQLITE_DRIVER_PREFIX):
        return create_engine(database_url)

    # FastAPI runs sync endpoints in a thread pool, so connections cross threads.
    connect_args = {"check_same_thread": False}
    if url.database in (None, "", SQLITE_MEMORY_DATABASE):
        return create_engine(database_url, connect_args=connect_args, poolclass=StaticPool)

    Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, connect_args=connect_args)


def init_database(engine: Engine) -> None:
    """Create missing tables and seed the default rules when the rule table is empty."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(RuleRecord.id).limit(1)).first() is not None:
            return
        session.add_all(RuleRecord(title=title, text=text) for title, text in DEFAULT_RULES)
        session.commit()
    logger.info("database seeded with default rules", extra={"rule_count": len(DEFAULT_RULES)})
