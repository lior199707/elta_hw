from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect
from sqlmodel import Session, select

from doc_checker.repository.database import create_db_engine, init_database
from doc_checker.repository.db_models import RuleRecord
from doc_checker.repository.default_rules import DEFAULT_RULES


def _rule_titles(engine_url: str) -> list[str]:
    engine = create_db_engine(engine_url)
    with Session(engine) as session:
        return [rule.title for rule in session.exec(select(RuleRecord)).all()]


def test_fresh_clone_creates_directory_file_tables_and_default_rules(tmp_path: Path) -> None:
    database_file = tmp_path / "not" / "yet" / "created" / "doc_checker.db"
    engine = create_db_engine(f"sqlite:///{database_file}")

    init_database(engine)

    assert database_file.is_file()
    assert {"rule", "check_run"} <= set(inspect(engine).get_table_names())
    assert _rule_titles(f"sqlite:///{database_file}") == [title for title, _ in DEFAULT_RULES]


def test_restart_does_not_duplicate_default_rules(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'doc_checker.db'}"

    init_database(create_db_engine(url))
    init_database(create_db_engine(url))

    assert len(_rule_titles(url)) == len(DEFAULT_RULES)


def test_user_rules_are_not_mixed_with_defaults_on_restart(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'doc_checker.db'}"
    engine = create_db_engine(url)
    init_database(engine)
    with Session(engine) as session:
        for rule in session.exec(select(RuleRecord)).all():
            session.delete(rule)
        session.add(RuleRecord(title="Mine", text="My only rule."))
        session.commit()

    init_database(create_db_engine(url))

    assert _rule_titles(url) == ["Mine"]


def test_in_memory_engine_shares_data_between_sessions() -> None:
    engine = create_db_engine("sqlite:///:memory:")
    init_database(engine)

    with Session(engine) as first:
        first.add(RuleRecord(title="Extra", text="Extra rule."))
        first.commit()
    with Session(engine) as second:
        titles = [rule.title for rule in second.exec(select(RuleRecord)).all()]

    assert "Extra" in titles
