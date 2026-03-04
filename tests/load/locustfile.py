"""
Locust нагрузочное тестирование для pattern-service.

Запуск:
    # Установка
    pip install locust

    # Web UI (http://localhost:8089)
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Headless (CLI)
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
        --headless -u 100 -r 10 --run-time 60s

Сценарии:
    - ReadHeavyUser: 80% чтение, 20% запись (типичный web-сервис)
    - WriteHeavyUser: 50% чтение, 50% запись (batch import сценарий)
"""

from __future__ import annotations

import random
import string
import uuid

from locust import HttpUser, between, task


def _random_email() -> str:
    """Сгенерировать случайный email."""
    name = "".join(random.choices(string.ascii_lowercase, k=8))
    domain = random.choice(["example.com", "test.org", "demo.io"])
    return f"{name}@{domain}"


def _random_name() -> str:
    """Сгенерировать случайное имя."""
    first = random.choice(["Иван", "Мария", "Пётр", "Анна", "Дмитрий", "Елена", "Алексей"])
    last = random.choice(["Иванов", "Петрова", "Сидоров", "Козлова", "Михайлов", "Новикова"])
    return f"{first} {last}"


class ReadHeavyUser(HttpUser):
    """
    Сценарий: 80% чтение, 20% запись.
    Типичная нагрузка web-приложения.
    """

    wait_time = between(0.1, 0.5)
    weight = 8  # 80% пользователей

    def on_start(self):
        """Создать тестового пользователя при старте."""
        self._created_ids: list[str] = []
        resp = self.client.post(
            "/api/v1/users/",
            json={"email": _random_email(), "name": _random_name()},
        )
        if resp.status_code == 201:
            self._created_ids.append(resp.json()["id"])

    @task(5)
    def list_users(self):
        """GET /api/v1/users/ — список с пагинацией."""
        page = random.randint(1, 5)
        self.client.get(f"/api/v1/users/?page={page}&page_size=50")

    @task(3)
    def list_users_cursor(self):
        """GET /api/v1/users/cursor — cursor-based пагинация."""
        self.client.get("/api/v1/users/cursor?limit=50")

    @task(3)
    def get_user(self):
        """GET /api/v1/users/{id} — получить пользователя."""
        if self._created_ids:
            user_id = random.choice(self._created_ids)
            self.client.get(f"/api/v1/users/{user_id}")

    @task(1)
    def create_user(self):
        """POST /api/v1/users/ — создать пользователя."""
        resp = self.client.post(
            "/api/v1/users/",
            json={"email": _random_email(), "name": _random_name()},
        )
        if resp.status_code == 201:
            self._created_ids.append(resp.json()["id"])
            # Не накапливаем слишком много
            if len(self._created_ids) > 100:
                self._created_ids = self._created_ids[-50:]

    @task(1)
    def get_nonexistent(self):
        """GET /api/v1/users/{id} — 404 сценарий."""
        fake_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/v1/users/{fake_id}",
            catch_response=True,
        ) as resp:
            if resp.status_code == 404:
                resp.success()

    @task(1)
    def health_check(self):
        """GET /health/readiness — проверка здоровья."""
        self.client.get("/health/readiness")


class WriteHeavyUser(HttpUser):
    """
    Сценарий: 50% чтение, 50% запись.
    Имитация batch-импорта / активного CRUD.
    """

    wait_time = between(0.05, 0.2)
    weight = 2  # 20% пользователей

    def on_start(self):
        self._created_ids: list[str] = []

    @task(2)
    def create_user(self):
        """POST /api/v1/users/ — создать пользователя."""
        resp = self.client.post(
            "/api/v1/users/",
            json={"email": _random_email(), "name": _random_name()},
        )
        if resp.status_code == 201:
            self._created_ids.append(resp.json()["id"])
            if len(self._created_ids) > 200:
                self._created_ids = self._created_ids[-100:]

    @task(1)
    def update_user(self):
        """PATCH /api/v1/users/{id} — обновить пользователя."""
        if self._created_ids:
            user_id = random.choice(self._created_ids)
            self.client.patch(
                f"/api/v1/users/{user_id}",
                json={"name": _random_name()},
            )

    @task(1)
    def delete_user(self):
        """DELETE /api/v1/users/{id} — удалить пользователя."""
        if self._created_ids:
            user_id = self._created_ids.pop(0)
            with self.client.delete(
                f"/api/v1/users/{user_id}",
                catch_response=True,
            ) as resp:
                if resp.status_code in (204, 404):
                    resp.success()

    @task(2)
    def list_users(self):
        """GET /api/v1/users/ — список."""
        self.client.get("/api/v1/users/?page=1&page_size=50")

