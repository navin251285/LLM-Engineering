# A stand-in streaming engine for lesson 07. It is NOT a language model.
import asyncio, json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
ENGINE = json.loads((Path(__file__).parent / "settings.json").read_text())
app = FastAPI()
slots = asyncio.Semaphore(ENGINE["max_running"])
state = {"running": 0}
@app.get("/health")
async def health(): return {"ok": True}
@app.post("/generate")
async def generate(req: dict):
    async def stream():
        async with slots:                # waiting here is queueing: it shows up in TTFT
            state["running"] += 1
            try:
                await asyncio.sleep(req["prompt_tokens"] / 1000 * ENGINE["prefill_ms_per_1k_tokens"] / 1000)
                for i in range(req["output_tokens"]):
                    if i:                # one decode step: a fixed base plus a cost per running request
                        step_ms = ENGINE["decode_base_ms"] + ENGINE["decode_ms_per_running"] * state["running"]
                        await asyncio.sleep(step_ms / 1000)
                    yield f"data: {json.dumps({'token': i})}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                state["running"] -= 1
    return StreamingResponse(stream(), media_type="text/event-stream")
