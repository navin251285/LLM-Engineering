"""Step 1: the health check, the page, and one question answered by the engine.

The engine call is recorded once with llm_replay (tests/cassettes/test_step1_ask.yaml)
and replayed offline. Re-record with: TUT_LLM_MODE=record <venv python> -m pytest tests/test_step1_ask.py
"""
import socket

import llm_replay
from fastapi.testclient import TestClient

from brightside_desk.api import create_app
from brightside_desk.config import Settings, get_settings

QUESTION = "Can I return an opened item?"


def test_health_and_page_are_served():
    client = TestClient(create_app())
    assert client.get("/health").json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "/ask" in page.text


def test_empty_question_is_rejected_before_the_engine():
    client = TestClient(create_app())
    assert client.post("/ask", json={"question": "   "}).status_code == 422


def test_engine_that_is_down_gives_503():
    with socket.socket() as s:                       # a port that nothing listens on
        s.bind(("127.0.0.1", 0))
        closed = s.getsockname()[1]
    settings = Settings(vllm_base_url=f"http://127.0.0.1:{closed}/v1", vllm_api_key="", model="x",
                        timeout_s=5, max_tokens=20, port=8980)
    client = TestClient(create_app(settings=settings))
    r = client.post("/ask", json={"question": QUESTION})
    assert r.status_code == 503
    assert "not answering" in r.json()["detail"]


def test_ask_returns_the_engines_answer():
    settings = get_settings()
    llm_replay.start("test_step1_ask")               # recorded once, replayed offline
    try:
        r = TestClient(create_app(settings=settings)).post("/ask", json={"question": QUESTION})
    finally:
        llm_replay.stop()
    assert r.status_code == 200
    body = r.json()
    assert body["answer"]
    assert "30" in body["answer"]                    # the policy's 30-day return window
    assert body["model"] == settings.model
    assert body["prompt_tokens"] > 0 and body["completion_tokens"] > 0
