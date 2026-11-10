from __future__ import annotations

import pytest
from sqlmodel import Session

from doc_checker.repository.default_rules import DEFAULT_RULES
from doc_checker.repository.repository_errors import RecordNotFoundError
from doc_checker.repository.rule_repository import RuleRepository


@pytest.fixture
def rules(session: Session) -> RuleRepository:
    return RuleRepository(session)


def test_lists_seeded_rules_oldest_first(rules: RuleRepository) -> None:
    assert [rule.title for rule in rules.list_rules()] == [title for title, _ in DEFAULT_RULES]


def test_create_and_get(rules: RuleRepository) -> None:
    created = rules.create("New", "New rule text.", is_active=False)

    fetched = rules.get(created.id or 0)

    assert (fetched.title, fetched.text, fetched.is_active) == ("New", "New rule text.", False)


def test_list_active_only_skips_inactive_rules(rules: RuleRepository) -> None:
    rules.create("Off", "Inactive rule.", is_active=False)

    assert "Off" not in [rule.title for rule in rules.list_rules(active_only=True)]
    assert "Off" in [rule.title for rule in rules.list_rules()]


def test_update_changes_only_given_fields_and_bumps_updated_at(rules: RuleRepository) -> None:
    rule = rules.create("Title", "Text.")
    before = rule.updated_at

    updated = rules.update(rule.id or 0, is_active=False)

    assert (updated.title, updated.text, updated.is_active) == ("Title", "Text.", False)
    assert updated.updated_at > before


def test_delete_removes_the_rule(rules: RuleRepository) -> None:
    rule = rules.create("Gone", "Soon gone.")

    rules.delete(rule.id or 0)

    with pytest.raises(RecordNotFoundError):
        rules.get(rule.id or 0)


@pytest.mark.parametrize("action", ["get", "update", "delete"])
def test_missing_rule_raises_not_found(rules: RuleRepository, action: str) -> None:
    with pytest.raises(RecordNotFoundError):
        if action == "update":
            rules.update(999, title="x")
        else:
            getattr(rules, action)(999)


def test_get_many_keeps_requested_order(rules: RuleRepository) -> None:
    assert [rule.id for rule in rules.get_many([3, 1])] == [3, 1]


def test_get_many_names_every_missing_id(rules: RuleRepository) -> None:
    with pytest.raises(RecordNotFoundError) as exc_info:
        rules.get_many([1, 998, 999])

    assert "998" in str(exc_info.value)
    assert "999" in str(exc_info.value)
