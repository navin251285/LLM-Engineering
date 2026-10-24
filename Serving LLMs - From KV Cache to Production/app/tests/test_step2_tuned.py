"""Step 2: engine settings from the config, latency metrics (TTFT, TPOT, SLO) and their tests.

The streamed answers are recorded once with llm_replay (tests/cassettes/test_step2_ask_stream.yaml)
and replayed offline. Re-record with:
    TUT_LLM_MODE=record <venv python> -m pytest tests/test_step2_tuned.py::test_ask_streams_and_reports_latency
"""
import socket

import llm_replay
import pytest
from fastapi.testclient import TestClient

from brightside_desk.api import create_app
from brightside_desk.config import Settings, get_settings
from brightside_desk.metrics import LatencyStats, Timing, percentile, timing_from_arrivals

QUESTION = "Can I return an opened item?"


def _settings(**overrides) -> Settings:
    base = dict(vllm_base_url="http://127.0.0.1:1/v1", vllm_api_key="", model="m", timeout_s=5,
                max_tokens=20, port=8980, max_model_len=2048, slo_ttft_s=2.0, slo_tpot_ms=15.0, stats_window=10)
    base.update(overrides)
    return Settings(**base)


def test_settings_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("BRIGHTSIDE_MAX_TOKENS", "40")
    monkeypatch.setenv("BRIGHTSIDE_SLO_TTFT_S", "1.5")
    settings = get_settings()
    assert settings.max_tokens == 40
    assert settings.slo_ttft_s == 1.5
    assert settings.max_model_len > 0 and settings.slo_tpot_ms > 0


def test_settings_endpoint_shows_targets_but_not_the_key_or_the_address():
    settings = _settings(vllm_api_key="test-only-value")
    body = TestClient(create_app(settings=settings)).get("/settings").json()
    assert body["max_tokens"] == 20 and body["max_model_len"] == 2048
    assert body["slo"] == {"ttft_s": 2.0, "tpot_ms": 15.0}
    assert "test-only-value" not in str(body)
    assert "127.0.0.1" not in str(body)


def test_percentile_is_nearest_rank():
    values = [10, 20, 30, 40, 50]
    assert percentile(values, 50) == 30
    assert percentile(values, 95) == 50
    assert percentile([], 50) is None


def test_timing_splits_ttft_total_and_tpot():
    # first token at 200 ms, then four more tokens every 50 ms: 5 tokens in all
    timing = timing_from_arrivals([0.2, 0.25, 0.3, 0.35, 0.4], n_tokens=5)
    assert timing.ttft_ms == pytest.approx(200)
    assert timing.total_ms == pytest.approx(400)
    assert timing.tpot_ms == pytest.approx(50)


def test_one_token_answer_has_no_tpot():
    assert timing_from_arrivals([0.3], n_tokens=1).tpot_ms is None
    with pytest.raises(ValueError):
        timing_from_arrivals([], n_tokens=0)


def test_slo_counts_only_answers_that_meet_both_targets():
    stats = LatencyStats(window=10, slo_ttft_s=0.5, slo_tpot_ms=15)
    stats.record(Timing(ttft_ms=300, total_ms=900, tpot_ms=10))    # meets both
    stats.record(Timing(ttft_ms=800, total_ms=1000, tpot_ms=5))    # misses the first-token target
    stats.record(Timing(ttft_ms=200, total_ms=900, tpot_ms=30))    # misses the per-token target
    summary = stats.summary()
    assert summary["answers"] == 3
    assert summary["within_slo"] == pytest.approx(1 / 3, abs=1e-3)


def test_window_keeps_only_the_recent_answers():
    stats = LatencyStats(window=2, slo_ttft_s=2.0, slo_tpot_ms=15)
    for ttft in (100, 200, 300):
        stats.record(Timing(ttft_ms=ttft, total_ms=ttft + 50, tpot_ms=None))
    summary = stats.summary()
    assert summary["answers"] == 2
    assert summary["ttft_ms_p50"] == 200


def test_engine_down_gives_503_and_counts_an_error():
    with socket.socket() as s:                       # a port that nothing listens on
        s.bind(("127.0.0.1", 0))
        closed = s.getsockname()[1]
    client = TestClient(create_app(settings=_settings(vllm_base_url=f"http://127.0.0.1:{closed}/v1")))
    assert client.post("/ask", json={"question": QUESTION}).status_code == 503
    assert client.get("/stats").json()["errors"] == 1


def test_ask_streams_and_reports_latency():
    settings = get_settings()
    llm_replay.start("test_step2_ask_stream")        # recorded once, replayed offline
    try:
        client = TestClient(create_app(settings=settings))
        first = client.post("/ask", json={"question": QUESTION}).json()
        second = client.post("/ask", json={"question": "How long do refunds take?"}).json()
        stats = client.get("/stats").json()
    finally:
        llm_replay.stop()
    assert "30" in first["answer"]                   # the policy's 30-day return window
    for body in (first, second):
        assert body["answer"]
        assert 0 < body["ttft_ms"] <= body["total_ms"]
        assert body["tpot_ms"] is not None and body["tpot_ms"] > 0
        assert body["prompt_tokens"] > 0 and body["completion_tokens"] > 0
    assert stats["answers"] == 2 and stats["errors"] == 0
    assert stats["ttft_ms_p50"] > 0 and stats["tpot_ms_p50"] > 0
