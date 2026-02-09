"""Shared test configuration.

Patches PostgreSQL-specific server defaults to work with SQLite for testing.
"""


def patch_pg_server_defaults():
    """Replace PostgreSQL-specific server_defaults with SQLite-compatible ones.

    Called before create_all in integration tests.
    """
    from app.database import Base

    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                try:
                    default_text = str(column.server_default.arg)
                except (AttributeError, TypeError):
                    continue
                if "gen_random_uuid()" in default_text:
                    # Remove the PG-specific server default; rely on Python-side default
                    column.server_default = None
