"""SIMULATED vLLM replica for lesson 33. It runs NO model: it takes time, applies a queue limit like
vLLM's --max-num-queued-reqs (rejects with HTTP 503), and exposes vLLM metric names on /metrics."""
import asyncio, os, sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest

NAME = sys.argv[1] if len(sys.argv) > 1 else "sim"
SLOTS, QUEUE_LIMIT = 4, int(os.environ.get("QUEUE_LIMIT", "8"))   # decode slots; requests allowed in the system (running + waiting)
PREFILL_MS, DECODE_MS = 0.2, 5.0                                   # simulated ms per prompt token, per output token
MODEL = "brightside-qwen-0.5b"
REG = CollectorRegistry()
RUNNING = Gauge("vllm:num_requests_running", "Requests in the batch", registry=REG)
WAITING = Gauge("vllm:num_requests_waiting", "Requests waiting for a slot", registry=REG)
KV_USE = Gauge("vllm:kv_cache_usage_perc", "KV cache usage (0 to 1)", registry=REG)
# prometheus_client adds _total on the page: vllm:admission_rejections_total{reason=...}
REJECT = Counter("vllm:admission_rejections", "Number of admission attempts rejected by a queue limit, by reason.",
                 ["model_name", "reason"], registry=REG)
SUCCESS = Counter("vllm:request_success", "Finished requests", registry=REG)
REJECT.labels(model_name=MODEL, reason="max_num_queued_reqs")     # show the series from the start, at 0
SLOT, IN_SYSTEM = asyncio.Semaphore(SLOTS), [0]
app = FastAPI()

@app.get("/health")
def health():
    return PlainTextResponse("ok")

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    words = " ".join(m["content"] for m in body["messages"]).split()
    n_out = int(body.get("max_tokens", 32))
    if IN_SYSTEM[0] + 1 > QUEUE_LIMIT:                             # admission control: reject early, do not queue
        REJECT.labels(model_name=MODEL, reason="max_num_queued_reqs").inc()
        return JSONResponse(status_code=503, content={"error": {"message": "queue full, retry on another instance",
                            "type": "ServiceUnavailable", "code": 503}})
    IN_SYSTEM[0] += 1; WAITING.inc()
    try:
        async with SLOT:
            WAITING.dec(); RUNNING.inc()
            await asyncio.sleep((len(words) * PREFILL_MS + n_out * DECODE_MS) / 1000)
            RUNNING.dec()
    finally:
        IN_SYSTEM[0] -= 1
    SUCCESS.inc()
    return {"id": f"sim-{NAME}", "object": "chat.completion", "model": body.get("model"), "replica": NAME,
            "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant", "content": f"[SIMULATED replica {NAME}: no model ran]"}}],
            "usage": {"prompt_tokens": len(words), "completion_tokens": n_out, "total_tokens": len(words) + n_out}}

@app.get("/metrics")
def metrics():
    KV_USE.set(min(1.0, IN_SYSTEM[0] / QUEUE_LIMIT))
    return PlainTextResponse(generate_latest(REG).decode(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
