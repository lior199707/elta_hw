from __future__ import annotations


class RepositoryError(Exception):
    """Base for persistence-level failures."""


class RecordNotFoundError(RepositoryError):
    """A requested record does not exist."""
