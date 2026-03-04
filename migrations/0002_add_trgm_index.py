"""
Add pg_trgm GIN index for efficient ILIKE search on users.name
"""

from yoyo import step

__depends__ = {"0001_initial_schema"}

steps = [
    step(
        """
        CREATE EXTENSION IF NOT EXISTS pg_trgm;

        CREATE INDEX IF NOT EXISTS idx_users_name_trgm
            ON users USING GIN (name gin_trgm_ops);
        """,
        """
        DROP INDEX IF EXISTS idx_users_name_trgm;
        -- Не удаляем расширение pg_trgm, т.к. оно может использоваться другими таблицами
        """
    ),
]

