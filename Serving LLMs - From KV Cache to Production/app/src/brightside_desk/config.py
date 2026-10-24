"""Settings for the app, read from the course's environment and .env file.

The app reads the same `.env` as the notebooks, through the course's `tut_env.py`
(real environment first, then `.env`, placeholders count as not set). Nothing
secret or machine-specific is typed into the code.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# app/src/brightside_desk/config.py -> parents[3] is the course folder (where .env and tut_env.py live)
COURSE_DIR = Path(__file__).resolve().parents[3]
if str(COURSE_DIR) not in sys.path:
    sys.path.insert(0, str(COURSE_DIR))

from tut_env import env  # noqa: E402  (needs COURSE_DIR on sys.path first)


@dataclass(frozen=True)
class Settings:
    """Everything the API needs to reach the engine, and the targets it is measured against."""

    vllm_base_url: str       # OpenAI-compatible route of the engine, ends in /v1 (lesson 08)
    vllm_api_key: str        # empty when the engine runs without a key
    model: str               # the name the engine serves (the served-model-name)
    timeout_s: float         # how long one answer may take before the app gives up
    max_tokens: int          # answer length limit (lesson 08 uses 60)
    port: int                # port for `python -m brightside_desk` (the course's app range starts at 8980)
    max_model_len: int = 2048      # the engine's --max-model-len, the tuned value of lesson 16
    slo_ttft_s: float = 2.0        # target for the time to first token, p50 (lesson 18)
    slo_tpot_ms: float = 15.0      # target for the time per output token (lesson 07)
    stats_window: int = 200        # how many recent answers /stats summarises


def get_settings() -> Settings:
    """Read the settings now (call it again after changing .env)."""
    return Settings(
        vllm_base_url=env("VLLM_BASE_URL", "http://localhost:8000/v1"),
        vllm_api_key=env("VLLM_API_KEY", ""),
        model=env("BRIGHTSIDE_MODEL", "brightside-qwen-0.5b"),
        timeout_s=float(env("BRIGHTSIDE_TIMEOUT_S", "300")),   # a CPU engine's first answer can take minutes (lesson 08)
        max_tokens=int(env("BRIGHTSIDE_MAX_TOKENS", "60")),
        port=int(env("BRIGHTSIDE_PORT", "8980")),
        max_model_len=int(env("BRIGHTSIDE_MAX_MODEL_LEN", "2048")),  # must match the engine's --max-model-len
        slo_ttft_s=float(env("BRIGHTSIDE_SLO_TTFT_S", "2.0")),       # lesson 18's target on the lab CPU
        slo_tpot_ms=float(env("BRIGHTSIDE_SLO_TPOT_MS", "15")),      # lesson 07's target
        stats_window=int(env("BRIGHTSIDE_STATS_WINDOW", "200")),
    )
