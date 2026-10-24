"""The FastAPI app: /health, /ask, /settings, /stats, and the one-page UI at /.

Run it from app/src:  uvicorn brightside_desk.api:app --reload --port 8980
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import APIConnectionError, APIStatusError, OpenAI
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .config import Settings, get_settings
from .engine import EmptyAnswerError, ask, make_client
from .metrics import LatencyStats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("brightside_desk")

STATIC_DIR = Path(__file__).resolve().parent / "static"


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=3, max_length=1000, description="The customer's question")


class AskResponse(BaseModel):
    answer: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    ttft_ms: float = Field(description="Time to the first token, measured at the client (lesson 07)")
    tpot_ms: float | None = Field(description="Mean time per output token after the first; None for a one-token answer")
    total_ms: float = Field(description="Time to the last token")


def create_app(settings: Settings | None = None, client: OpenAI | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings and client; the server uses the defaults."""
    settings = settings or get_settings()
    client = client or make_client(settings)
    stats = LatencyStats(settings.stats_window, settings.slo_ttft_s, settings.slo_tpot_ms)
    app = FastAPI(title="Brightside support desk", version=__version__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/settings")
    def engine_settings() -> dict:
        """The tuned settings the app runs with. The key and the engine address are never shown."""
        return {
            "model": settings.model,
            "max_tokens": settings.max_tokens,
            "max_model_len": settings.max_model_len,
            "timeout_s": settings.timeout_s,
            "slo": {"ttft_s": settings.slo_ttft_s, "tpot_ms": settings.slo_tpot_ms},
        }

    @app.post("/ask", response_model=AskResponse)
    def ask_question(body: AskRequest) -> AskResponse:
        try:
            answer = ask(client, settings, body.question)
        except APIConnectionError:
            stats.record_error()
            log.warning("engine not reachable")
            raise HTTPException(503, "The engine is not answering. Start it, then ask again (see app/GUIDE.md).")
        except APIStatusError as exc:
            stats.record_error()
            log.error("engine returned HTTP %s", exc.status_code)
            raise HTTPException(502, f"The engine returned HTTP {exc.status_code}.")
        except EmptyAnswerError:
            stats.record_error()
            raise HTTPException(502, "The engine returned an empty answer.")
        stats.record(answer.timing)
        if answer.prompt_tokens + answer.completion_tokens > settings.max_model_len:
            log.warning("prompt and answer are longer than the engine's length limit (%d)", settings.max_model_len)
        return AskResponse(
            answer=answer.text,
            model=answer.model,
            prompt_tokens=answer.prompt_tokens,
            completion_tokens=answer.completion_tokens,
            ttft_ms=round(answer.timing.ttft_ms, 1),
            tpot_ms=None if answer.timing.tpot_ms is None else round(answer.timing.tpot_ms, 1),
            total_ms=round(answer.timing.total_ms, 1),
        )

    @app.get("/stats")
    def latency_stats() -> dict:
        """Latency over the most recent answers: p50 and p95 of TTFT and TPOT, and the share within the targets."""
        return stats.summary()

    @app.get("/", include_in_schema=False)
    def page() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    return app


app = create_app()
