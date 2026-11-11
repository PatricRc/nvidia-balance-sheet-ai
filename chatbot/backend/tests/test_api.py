import json

from fastapi.testclient import TestClient

from app import main

from .fakes import FakeAnthropic, text_turn


def test_chat_streams_sse_and_rate_limits(monkeypatch):
    with TestClient(main.app) as client:
        main.app.state.agent.client = FakeAnthropic([text_turn("Hello.")] * 10)
        main.app.state.guard.per_minute = 2
        assert client.get("/api/health").json()["measures"] == 84
        r = client.post("/api/chat", json={"question": "hi"})
        events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]
        assert r.headers["content-type"].startswith("text/event-stream")
        assert events[-1]["type"] == "done"
        client.post("/api/chat", json={"question": "hi"})
        assert client.post("/api/chat", json={"question": "hi"}).status_code == 429
        assert client.post("/api/chat", json={"question": ""}).status_code == 422
        assert client.get("/").status_code == 200  # chat UI served
