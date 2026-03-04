"""
Seed admin user with all permissions.

Creates:
  - System permissions (manage_permissions, manage_users, read_users, read_permissions)
  - Admin user (username: admin, email: admin@example.com, password: Admin1234!)
  - Assigns all permissions to admin user

Admin credentials:
  username : admin
  password : Admin1234!

Change the password immediately after first login in production.
"""

from yoyo import step

__depends__ = {"20260304_03_aB3cD-create-permissions"}

# ---------------------------------------------------------------------------
# Permissions to create
# ---------------------------------------------------------------------------
PERMISSIONS = [
    {
        "name": "Управление разрешениями",
        "code": "manage_permissions",
        "description": "Создание, изменение, удаление и назначение разрешений пользователям",
    },
    {
        "name": "Управление пользователями",
        "code": "manage_users",
        "description": "Создание и редактирование учётных записей пользователей",
    },
    {
        "name": "Просмотр пользователей",
        "code": "read_users",
        "description": "Просмотр списка и профилей пользователей",
    },
    {
        "name": "Просмотр разрешений",
        "code": "read_permissions",
        "description": "Просмотр списка всех разрешений системы",
    },
]

# ---------------------------------------------------------------------------
# Admin account defaults — override via env if needed
# ---------------------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_FIRST_NAME = "Admin"
ADMIN_LAST_NAME = "User"
ADMIN_PASSWORD = "Admin1234!"


def _hash_password(plain: str) -> str:
    """Hash password with Argon2id using the same parameters as the app."""
    from argon2 import PasswordHasher

    ph = PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,
        salt_len=16,
    )
    return ph.hash(plain)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------
def apply(conn):
    cursor = conn.cursor()

    # 1. Insert permissions (skip if already exist)
    permission_ids: list[int] = []
    for perm in PERMISSIONS:
        cursor.execute(
            """
            INSERT INTO permissions (name, code, description, is_active)
            VALUES (%(name)s, %(code)s, %(description)s, TRUE)
            ON CONFLICT (code) DO UPDATE
                SET name        = EXCLUDED.name,
                    description = EXCLUDED.description,
                    is_active   = TRUE
            RETURNING id;
            """,
            perm,
        )
        row = cursor.fetchone()
        permission_ids.append(row[0])

    # 2. Create admin user (skip if username already exists)
    password_hash = _hash_password(ADMIN_PASSWORD)
    cursor.execute(
        """
        INSERT INTO users (first_name, last_name, username, email, password, is_active, is_superuser)
        VALUES (%(first_name)s, %(last_name)s, %(username)s, %(email)s, %(password)s, TRUE, TRUE)
        ON CONFLICT (username) DO UPDATE
            SET is_superuser = TRUE,
                is_active    = TRUE
        RETURNING id;
        """,
        {
            "first_name": ADMIN_FIRST_NAME,
            "last_name": ADMIN_LAST_NAME,
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "password": password_hash,
        },
    )
    row = cursor.fetchone()
    admin_id = row[0]

    # 3. Assign all permissions to admin user
    for perm_id in permission_ids:
        cursor.execute(
            """
            INSERT INTO user_permissions (user_id, permission_id)
            VALUES (%(user_id)s, %(permission_id)s)
            ON CONFLICT (user_id, permission_id) DO NOTHING;
            """,
            {"user_id": str(admin_id), "permission_id": perm_id},
        )

    cursor.close()


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------
def rollback(conn):
    cursor = conn.cursor()

    # Remove permission assignments for admin
    cursor.execute(
        """
        DELETE FROM user_permissions
        WHERE user_id = (SELECT id FROM users WHERE username = %(username)s);
        """,
        {"username": ADMIN_USERNAME},
    )

    # Remove admin user
    cursor.execute(
        "DELETE FROM users WHERE username = %(username)s;",
        {"username": ADMIN_USERNAME},
    )

    # Remove seeded permissions
    codes = [p["code"] for p in PERMISSIONS]
    cursor.execute(
        "DELETE FROM permissions WHERE code = ANY(%(codes)s);",
        {"codes": codes},
    )

    cursor.close()


steps = [step(apply, rollback)]

