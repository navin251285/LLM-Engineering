"""SIMULATED vLLM replica for lesson 31. It runs NO model. It answers /health 503 until SIM_COLD_START_S
seconds have passed (a stand-in for loading weights), has 4 decode slots, and exposes vLLM metric names on /metrics."""
import asyncio, os, sys, time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest

NAME = sys.argv[1] if len(sys.argv) > 1 else "sim"
READY_AT = time.monotonic() + float(os.environ.get("SIM_COLD_START_S", "0"))
SLOTS, MS_PER_TOKEN, KV_PER_REQ = 4, 5.0, 0.25
REG = CollectorRegistry()
RUNNING = Gauge("vllm:num_requests_running", "Requests in the batch", registry=REG)
WAITING = Gauge("vllm:num_requests_waiting", "Requests waiting for a slot", registry=REG)
KV_USE = Gauge("vllm:kv_cache_usage_perc", "KV cache usage (0 to 1)", registry=REG)
SUCCESS = Counter("vllm:request_success", "Finished requests", registry=REG)   # _total on the page
SLOT, STATE = asyncio.Semaphore(SLOTS), {"running": 0, "waiting": 0}
app = FastAPI()

@app.get("/health")
def health():
    if time.monotonic() < READY_AT: return JSONResponse({"status": "loading"}, status_code=503)
    return {"status": "ok", "replica": NAME}

@app.post("/v1/chat/completions")
async def chat(req: Request):
    if time.monotonic() < READY_AT: return JSONResponse({"error": "loading"}, status_code=503)
    body = await req.json()
    n_out = int(body.get("max_tokens", 32))
    STATE["waiting"] += 1
    async with SLOT:                                          # waits here while all slots are busy
        STATE["waiting"] -= 1; STATE["running"] += 1
        await asyncio.sleep(n_out * MS_PER_TOKEN / 1000)      # simulated decode time, no model
        STATE["running"] -= 1
    SUCCESS.inc()
    return {"id": f"sim-{NAME}", "object": "chat.completion", "model": body.get("model"), "replica": NAME,
            "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant",
                         "content": f"[SIMULATED replica {NAME}: no model ran]"}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": n_out, "total_tokens": n_out}}

@app.get("/metrics")
def metrics():
    RUNNING.set(STATE["running"]); WAITING.set(STATE["waiting"])
    KV_USE.set(min(1.0, KV_PER_REQ * STATE["running"]))
    return PlainTextResponse(generate_latest(REG).decode(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
