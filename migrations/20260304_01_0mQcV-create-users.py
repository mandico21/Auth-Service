"""
create users
"""

from yoyo import step

__depends__ = {'__init__'}

steps = [
    step(
        """
        create table users
        (
            id           uuid primary key      default gen_random_uuid(),
            first_name   varchar(50)  not null,
            last_name    varchar(50)  not null,
            username     varchar(50)  not null unique,
            email        varchar(100) not null unique,
            password     text         not null,
            is_active    boolean      not null default true,
            is_superuser boolean      not null default false,
            created_at   timestamptz  not null default now(),
            updated_at   timestamptz  not null default now()
        );

        CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS TRIGGER AS
        $$
        BEGIN
            IF NEW IS DISTINCT FROM OLD THEN
                NEW.updated_at = now();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        create trigger trigger_carts_updated_at
            before update
            on users
            for each row
        execute function set_updated_at();
        """,
        """
        DROP FUNCTION IF EXISTS set_updated_at();
        DROP TABLE IF EXISTS users;
        """
    )
]
