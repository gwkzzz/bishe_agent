from __future__ import annotations

from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient) -> dict[str, str]:
    username = f"m2_{uuid4().hex}"
    registered = client.post(
        "/api/auth/register",
        json={"username": username, "password": "secret"},
    )
    assert registered.status_code == 201
    response = client.post("/api/auth/login", json={"username": username, "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_requires_registration() -> None:
    client = TestClient(app)
    username = f"missing_{uuid4().hex}"

    missing = client.post("/api/auth/login", json={"username": username, "password": "secret"})
    assert missing.status_code == 401

    registered = client.post(
        "/api/auth/register",
        json={"username": username, "password": "secret"},
    )
    assert registered.status_code == 201
    assert "id" not in registered.json()["user"]

    duplicate = client.post(
        "/api/auth/register",
        json={"username": username, "password": "secret"},
    )
    assert duplicate.status_code == 409

    logged_in = client.post("/api/auth/login", json={"username": username, "password": "secret"})
    assert logged_in.status_code == 200
    assert "id" not in logged_in.json()["user"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {logged_in.json()['access_token']}"})
    assert me.status_code == 200
    assert "id" not in me.json()


def test_auth_and_case_crud() -> None:
    client = TestClient(app)
    headers = _login(client)

    unauthorized = client.get("/api/cases")
    assert unauthorized.status_code == 401

    created = client.post(
        "/api/cases",
        json={"title": "拖欠工资", "summary": "公司拖欠两个月工资"},
        headers=headers,
    )
    assert created.status_code == 201
    case_id = created.json()["id"]

    listed = client.get("/api/cases", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == case_id for item in listed.json())

    patched = client.patch(
        f"/api/cases/{case_id}",
        json={"cause": "追索劳动报酬", "status": "open"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["cause"] == "追索劳动报酬"

    detail = client.get(f"/api/cases/{case_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == case_id


def test_chat_stream_persists_mock_result(monkeypatch) -> None:
    from app.api import chat as chat_module

    class FakeAlgorithmClient:
        async def analyze_case(self, payload, trace_id):
            return {
                "summary": "用户称公司拖欠工资",
                "cause": "追索劳动报酬",
                "confidence": 0.8,
                "answer": "根据你目前提供的信息，可能涉及追索劳动报酬。",
                "profile_candidates": [
                    {
                        "candidate_type": "fact",
                        "content_json": {"fact_text": "公司拖欠工资"},
                    }
                ],
            }

    monkeypatch.setattr(chat_module, "AlgorithmClient", FakeAlgorithmClient)

    client = TestClient(app)
    headers = _login(client)
    response = client.post(
        "/api/chat/stream",
        json={"message": "公司拖欠我两个月工资"},
        headers=headers,
    )
    assert response.status_code == 200
    assert "event: final" in response.text
    assert "追索劳动报酬" in response.text


def test_evidence_upload_analyze_and_task(monkeypatch) -> None:
    from app.api import evidence as evidence_module

    class FakeMinIOClient:
        def put_object(self, object_name, data, length, content_type):
            assert data.read() == b"hello"
            return f"minio://evidence/{object_name}"

    class FakeRedisClient:
        async def set_json(self, key, value, ttl_seconds=None):
            assert key.startswith("task:")

        async def close(self):
            return None

    class FakeRabbitMQPublisher:
        async def declare_queue(self, queue_name, durable=True):
            assert queue_name == "evidence.analyze"

        async def publish_json(self, routing_key, payload, exchange_name=""):
            assert routing_key == "evidence.analyze"

        async def close(self):
            return None

    monkeypatch.setattr(evidence_module, "MinIOClient", FakeMinIOClient)
    monkeypatch.setattr(evidence_module, "RedisClient", FakeRedisClient)
    monkeypatch.setattr(evidence_module, "RabbitMQPublisher", FakeRabbitMQPublisher)

    client = TestClient(app)
    headers = _login(client)
    case = client.post("/api/cases", json={"title": "证据测试"}, headers=headers).json()

    uploaded = client.post(
        "/api/evidence/upload",
        data={"case_id": case["id"], "name": "聊天记录", "evidence_type": "电子数据"},
        files={"file": ("chat.txt", BytesIO(b"hello"), "text/plain")},
        headers=headers,
    )
    assert uploaded.status_code == 201
    evidence_id = uploaded.json()["id"]

    listed = client.get(f"/api/cases/{case['id']}/evidence", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == evidence_id

    task = client.post(f"/api/evidence/{evidence_id}/analyze", headers=headers)
    assert task.status_code == 200
    task_id = task.json()["task_id"]

    fetched = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "pending"


def test_arbitration_document_generation(monkeypatch) -> None:
    from app.api import documents as documents_module

    class FakeAlgorithmClient:
        async def generate_arbitration_document(self, payload, trace_id):
            return {
                "title": "劳动仲裁申请书初稿",
                "content_md": "# 劳动仲裁申请书\n\n待补充",
                "status": "draft",
            }

    monkeypatch.setattr(documents_module, "AlgorithmClient", FakeAlgorithmClient)

    client = TestClient(app)
    headers = _login(client)
    case = client.post("/api/cases", json={"title": "文书测试"}, headers=headers).json()

    created = client.post(
        "/api/documents/arbitration",
        json={"case_id": case["id"]},
        headers=headers,
    )
    assert created.status_code == 200
    document_id = created.json()["id"]

    fetched = client.get(f"/api/documents/{document_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["content_md"].startswith("# 劳动仲裁申请书")
