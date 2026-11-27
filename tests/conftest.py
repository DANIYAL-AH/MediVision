from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


class _HealthyDB:
    def execute(self, statement):
        return 1


class _BrokenDB:
    def execute(self, statement):
        raise OperationalError("SELECT 1", {}, Exception("db down"))


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def _override_db():
        yield _HealthyDB()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def broken_db_client() -> Generator[TestClient, None, None]:
    def _override_db():
        yield _BrokenDB()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
