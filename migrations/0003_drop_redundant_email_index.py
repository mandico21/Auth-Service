"""
Drop redundant idx_users_email — the UNIQUE constraint on users.email
already creates a B-tree index automatically. A second explicit index
wastes disk space and slows down INSERT/UPDATE.
"""

from yoyo import step

__depends__ = {"0002_add_trgm_index"}

steps = [
    step(
        """
        DROP INDEX IF EXISTS idx_users_email;
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """
    ),
]

