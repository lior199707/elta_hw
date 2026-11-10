from __future__ import annotations

from collections.abc import Sequence

from sqlmodel import Session, col, select

from doc_checker.repository.db_models import RuleRecord, utc_now
from doc_checker.repository.repository_errors import RecordNotFoundError


class RuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_rules(self, active_only: bool = False) -> list[RuleRecord]:
        """All rules (or only active ones), oldest first."""
        statement = select(RuleRecord).order_by(col(RuleRecord.id))
        if active_only:
            statement = statement.where(col(RuleRecord.is_active).is_(True))
        return list(self._session.exec(statement).all())

    def get(self, rule_id: int) -> RuleRecord:
        """Raises RecordNotFoundError."""
        rule = self._session.get(RuleRecord, rule_id)
        if rule is None:
            raise RecordNotFoundError(f"Rule {rule_id} does not exist.")
        return rule

    def get_many(self, rule_ids: Sequence[int]) -> list[RuleRecord]:
        """Rules in the order of `rule_ids`; raises RecordNotFoundError naming every missing id."""
        found = {
            rule.id: rule
            for rule in self._session.exec(
                select(RuleRecord).where(col(RuleRecord.id).in_(rule_ids))
            ).all()
        }
        missing = [rule_id for rule_id in rule_ids if rule_id not in found]
        if missing:
            raise RecordNotFoundError(f"Rules do not exist: {', '.join(map(str, missing))}.")
        return [found[rule_id] for rule_id in rule_ids]

    def create(self, title: str, text: str, is_active: bool = True) -> RuleRecord:
        rule = RuleRecord(title=title, text=text, is_active=is_active)
        self._session.add(rule)
        self._session.commit()
        self._session.refresh(rule)
        return rule

    def update(
        self,
        rule_id: int,
        title: str | None = None,
        text: str | None = None,
        is_active: bool | None = None,
    ) -> RuleRecord:
        """Change only the given fields and bump `updated_at`. Raises RecordNotFoundError."""
        rule = self.get(rule_id)
        if title is not None:
            rule.title = title
        if text is not None:
            rule.text = text
        if is_active is not None:
            rule.is_active = is_active
        rule.updated_at = utc_now()
        self._session.add(rule)
        self._session.commit()
        self._session.refresh(rule)
        return rule

    def delete(self, rule_id: int) -> None:
        """Raises RecordNotFoundError."""
        self._session.delete(self.get(rule_id))
        self._session.commit()
