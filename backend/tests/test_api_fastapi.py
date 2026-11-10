"""FastAPI-Verdrahtung. Läuft nur, wenn FastAPI und httpx installiert sind (CI: pip install -e ".[dev]")."""

import pytest

from setup_agent import repository as R
from setup_agent.demo import seed

from .conftest import NOW
from .test_api import ADMIN, FakeVerifier

fastapi = pytest.importorskip("fastapi", reason="FastAPI nicht installiert – läuft in der CI")


class TestFastApiWiring:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from setup_agent.api import create_app

        repo = R.InMemoryRepository()
        seed(repo, NOW)
        app = create_app(repo, FakeVerifier(), clock=lambda: NOW)
        import setup_agent.api_core as core
        return TestClient(app), repo, core

    def test_routes(self, client):
        c, repo, _ = client
        r = c.get("/api/v1/streamers")
        assert r.status_code == 200 and r.json()["total"] == 2
        assert c.get("/api/v1/streamers/twitch-nachtfalke/setup").status_code == 200
        assert c.get("/api/v1/products", params={"category": "licht", "max_price": 12000}).json()["items"][0]["id"] == "elgato-key-light-mini"
        assert c.get("/api/v1/products/gibtsnicht").json()["error"]["code"] == "not_found"
        assert c.get("/api/v1/products", params={"max_price": -1}).status_code == 400
        assert c.get("/api/v1/openapi.json").status_code == 200

    def test_admin_routes(self, client):
        c, repo, _ = client
        assert c.get("/api/v1/admin/proposals").status_code == 401
        assert c.get("/api/v1/admin/proposals", headers={"Authorization": "Bearer user-token"}).status_code == 403
        r = c.post("/api/v1/admin/products", json={"manufacturer": "Rode", "model": "PSA1+", "category": "mikrofonarm"},
                   headers={"Authorization": ADMIN})
        assert r.status_code == 200, r.text
        r = c.post("/api/v1/admin/products", json={"manufacturer": "RODE", "model": "PSA-1+", "category": "mikrofonarm"},
                   headers={"Authorization": ADMIN})
        assert r.status_code == 409
