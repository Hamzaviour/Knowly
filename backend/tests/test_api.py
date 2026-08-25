import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "version" in data
        assert "environment" in data

    def test_health(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestDocuments:
    def test_list_empty(self, client):
        r = client.get("/api/v1/documents?workspace_id=test-ws-clear")
        assert r.status_code == 200
        assert r.json() == []

    def test_upload(self, client):
        files = {"file": ("hello.txt", b"hello world", "text/plain")}
        r = client.post("/api/v1/documents/upload", files=files)
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "hello.txt"
        assert data["file_size"] == 11
        assert data["chunks_count"] >= 1

    def test_list_after_upload(self, client):
        files = {"file": ("list-test.txt", b"x" * 100, "text/plain")}
        client.post("/api/v1/documents/upload", files=files)
        r = client.get("/api/v1/documents?workspace_id=test-ws-clear")
        assert r.status_code == 200
        docs = r.json()
        assert len(docs) >= 1
        assert any(d["title"] == "list-test.txt" for d in docs)


class TestAnalytics:
    def test_summary_empty(self, client):
        r = client.get("/api/v1/analytics/summary?workspace_id=test-ws-clear")
        assert r.status_code == 200
        data = r.json()
        assert data["total_documents"] == 0
        assert data["total_queries"] == 0


class TestWorkflows:
    def test_list_empty(self, client):
        r = client.get("/api/v1/workflows?workspace_id=test-ws-clear")
        assert r.status_code == 200
        assert r.json() == []

    def test_create(self, client):
        r = client.post(
            "/api/v1/workflows",
            json={
                "name": "test-wf",
                "workspace_id": "test-ws-clear",
                "trigger_type": "manual",
                "condition_rules": {},
                "actions": [],
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "created"


class TestComparison:
    def test_missing_fields(self, client):
        r = client.post("/api/v1/compare", json={})
        assert r.status_code == 422

    def test_not_found(self, client):
        r = client.post(
            "/api/v1/compare",
            json={
                "doc1_id": "nonexistent-1",
                "doc2_id": "nonexistent-2",
                "workspace_id": "test-ws-clear",
            },
        )
        assert r.status_code == 404


class TestChat:
    def test_missing_fields(self, client):
        r = client.post("/api/v1/chat", json={})
        assert r.status_code == 422

    def test_chat(self, client):
        r = client.post(
            "/api/v1/chat",
            json={"query": "hello", "workspace_id": "test-ws-clear"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "model_used" in data
        assert "tokens" in data


class TestReports:
    def test_export_markdown(self, client):
        r = client.post(
            "/api/v1/reports/export",
            json={
                "title": "Test",
                "markdown_content": "# Hello",
                "format": "markdown",
            },
        )
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/markdown")
        assert "# Hello" in r.text

    def test_export_non_markdown(self, client):
        r = client.post(
            "/api/v1/reports/export",
            json={
                "title": "Test",
                "markdown_content": "# Hello",
                "format": "docx",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "exported"


class TestAuth:
    def test_password_hash_roundtrip(self):
        from app.auth import hash_password, verify_password
        pw = "tp"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)
        assert not verify_password("wrong", hashed)

    def test_token_encode_decode(self):
        from app.auth import create_access_token, decode_token
        token = create_access_token("user-123")
        assert len(token) > 10
        uid = decode_token(token)
        assert uid == "user-123"

    def test_invalid_token(self):
        from app.auth import decode_token
        assert decode_token("bad.token.here") is None

    def test_api_key_generator(self):
        from app.auth import generate_api_key
        raw, hashed = generate_api_key()
        assert raw.startswith("kly_")
        assert len(hashed) == 64

    def test_auth_dependent(self, client, db):
        from app.auth import require_user
        # No auth header means anon allowed — no exception
        r = client.get("/api/v1/health")
        assert r.status_code == 200
