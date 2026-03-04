"""
create refresh_token
"""

from yoyo import step

__depends__ = {'20260304_01_0mQcV-create-users'}

steps = [
    step(
        """
        create table refresh_tokens
        (
            id         SERIAL PRIMARY KEY,
            user_id    uuid      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            jti        TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked    BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """,
        """
        drop table if exists refresh_tokens;
        """
    )
]
