"""
create permissions
"""

from yoyo import step

__depends__ = {'20260304_02_peQbL-create-refresh-token'}

steps = [
    step(
        """
        CREATE TABLE permissions
        (
            id          SERIAL PRIMARY KEY,
            name        TEXT        NOT NULL UNIQUE,
            code        TEXT        NOT NULL UNIQUE,
            description TEXT        NOT NULL DEFAULT '',
            is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TRIGGER trigger_permissions_updated_at
            BEFORE UPDATE
            ON permissions
            FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();

        CREATE TABLE user_permissions
        (
            user_id       UUID    NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            permission_id INTEGER NOT NULL REFERENCES permissions (id) ON DELETE CASCADE,
            assigned_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, permission_id)
        );
        """,
        """
        DROP TABLE IF EXISTS user_permissions;
        DROP TABLE IF EXISTS permissions;
        """
    )
]

