"""Ask the local engine one question through the OpenAI-compatible API (lessons 08 and 07).

The answer is streamed, so the app can time the first token and the gaps between tokens
at the client (lesson 07). The OpenAI SDK only needs a base_url to reach vLLM, so this code
is the same call the lessons make. Nothing here knows about FastAPI.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from openai import OpenAI

from .config import Settings
from .metrics import Timing, timing_from_arrivals

log = logging.getLogger(__name__)

# The Brightside policy from lesson 08. The model may answer only from it.
SYSTEM_PROMPT = (
    "You are the Brightside support desk. Answer in one or two short sentences, using only this policy. "
    "Policy: opened items can be returned within 30 days with the receipt. "
    "Refunds reach the card in 5 business days."
)


class EmptyAnswerError(RuntimeError):
    """The engine answered, but with no text."""


@dataclass(frozen=True)
class Answer:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    timing: Timing


def make_client(settings: Settings) -> OpenAI:
    """One client for the whole app. max_retries=0: a down engine is reported at once."""
    return OpenAI(
        base_url=settings.vllm_base_url,
        api_key=settings.vllm_api_key or "not-needed",   # a local server ignores the key when none is set
        timeout=settings.timeout_s,
        max_retries=0,
    )


def ask(client: OpenAI, settings: Settings, question: str) -> Answer:
    """Stream one answer, time it token by token, and return it. Errors are raised for the API layer to map."""
    t_send = time.perf_counter()
    stream = client.chat.completions.create(
        model=settings.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        max_tokens=settings.max_tokens,
        temperature=0,
        stream=True,
        stream_options={"include_usage": True},   # the last chunk carries the token counts (lesson 08, step 4)
    )
    pieces: list[str] = []
    arrivals: list[float] = []                    # seconds from the request send to each text chunk
    model, usage = settings.model, None
    for chunk in stream:
        model = chunk.model or model
        if chunk.choices and chunk.choices[0].delta.content:
            pieces.append(chunk.choices[0].delta.content)
            arrivals.append(time.perf_counter() - t_send)
        if chunk.usage:
            usage = chunk.usage
    text = "".join(pieces).strip()
    if not arrivals:
        raise EmptyAnswerError("the engine streamed no text")
    completion = usage.completion_tokens if usage else len(arrivals)
    answer = Answer(
        text=text,
        model=model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=completion,
        timing=timing_from_arrivals(arrivals, completion),
    )
    log.info("answered: TTFT %.0f ms, total %.0f ms, %d completion tokens",
             answer.timing.ttft_ms, answer.timing.total_ms, answer.completion_tokens)
    return answer
