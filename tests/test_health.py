import app.models  # noqa: F401
from app.database import Base


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_health_db_unavailable(broken_db_client):
    response = broken_db_client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_all_models_registered():
    assert len(Base.metadata.tables) == 16
