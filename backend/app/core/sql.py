"""Helpers for the few code paths that build SQL text by hand.

Most persistence goes through the ORM. A handful of partial-update helpers
build a ``SET`` clause from a caller-supplied mapping, which means column
*names* are interpolated into the statement while values stay bound. That is
safe only for as long as every caller supplies trusted keys.

``assert_known_columns`` removes that dependence on caller discipline: keys
are checked against the model's mapper before interpolation, so an unexpected
name fails loudly instead of reaching the database.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import inspect as sa_inspect


def assert_known_columns(model: type, keys: Iterable[str]) -> None:
    """Raise ``ValueError`` unless every key is a real column on ``model``.

    Args:
        model: A mapped SQLAlchemy class.
        keys: Column names about to be interpolated into a statement.
    """
    allowed = {col.key for col in sa_inspect(model).mapper.column_attrs}
    unknown = sorted(set(keys) - allowed)
    if unknown:
        raise ValueError(f"Refusing to build SQL for unknown {model.__name__} column(s): {', '.join(unknown)}")
