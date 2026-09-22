"""GET /health/ready must report 503 (not 500) when the database is unreachable."""

from __future__ import annotations

from sqlalchemy.exc import OperationalError

from services.api.app.main import app
from services.common.db import get_db


class _UnavailableSession:
    """Stands in for a Session whose connection to PostgreSQL is down."""

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def _override_get_db():
    return _UnavailableSession()


def test_ready_returns_503_when_database_is_unavailable(client):
    app.dependency_overrides[get_db] = _override_get_db
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "database unavailable"
