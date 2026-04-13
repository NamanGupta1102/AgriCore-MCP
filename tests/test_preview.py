"""
Tests for the web playground JSON API and static routes (Starlette TestClient on FastMCP sse_app).
"""
import os
import sys

import pytest
from starlette.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from server_main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app.sse_app())


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_preview_requires_query(client):
    r = client.post("/api/preview", json={})
    assert r.status_code == 400
    assert "query" in r.json().get("error", "").lower()


def test_preview_invalid_json(client):
    r = client.post(
        "/api/preview",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_preview_returns_chunks_and_markdown(client):
    r = client.post(
        "/api/preview",
        json={"query": "How do I manage early blight?", "plant": "tomato"},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("chunks"), list)
    assert "guidelines_markdown" in data
    assert data.get("hard_constraints_markdown") is None
    ids = [c.get("id", "") for c in data["chunks"]]
    assert any("guide_tomato_blight" in i for i in ids), f"unexpected chunk ids: {ids}"


def test_playground_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"AgriCore" in r.content


def test_playground_assets(client):
    css = client.get("/assets/styles.css")
    js = client.get("/assets/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert b"body" in css.content or b"root" in css.content
    assert b"preview-form" in js.content
