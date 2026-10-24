"""SIMULATED vLLM replica for lesson 30. It runs NO model: it takes time, keeps a prefix cache of
16-token blocks and exposes vLLM metric names on /metrics. One word counts as one token."""
import asyncio, hashlib, sys
from collections import OrderedDict
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest

NAME = sys.argv[1] if len(sys.argv) > 1 else "sim"
BLOCK, SLOTS, KV_CAPACITY, CACHE_BLOCKS = 16, 4, 12000, 200   # block size, decode slots, KV tokens, cached blocks
PREFILL_MS, DECODE_MS = 0.2, 5.0                              # simulated ms per uncached prompt token, per output token
REG = CollectorRegistry()
RUNNING = Gauge("vllm:num_requests_running", "Requests in the batch", registry=REG)
WAITING = Gauge("vllm:num_requests_waiting", "Requests waiting for a slot", registry=REG)
KV_USE = Gauge("vllm:kv_cache_usage_perc", "KV cache usage (0 to 1)", registry=REG)
# prometheus_client adds _total on the page: vllm:prefix_cache_queries_total
QUERIES = Counter("vllm:prefix_cache_queries", "Prompt tokens queried against the prefix cache", registry=REG)
HITS = Counter("vllm:prefix_cache_hits", "Prompt tokens found in the prefix cache", registry=REG)
SUCCESS = Counter("vllm:request_success", "Finished requests", registry=REG)
SLOT, CACHE, IN_FLIGHT = asyncio.Semaphore(SLOTS), OrderedDict(), [0]   # CACHE: block hash -> None, least recent first

def block_hashes(words):                                      # full blocks only, a hash chain as in lesson 14
    out, parent = [], b""
    for i in range(0, len(words) - BLOCK + 1, BLOCK):
        parent = hashlib.sha256(parent + " ".join(words[i:i + BLOCK]).encode()).digest()
        out.append(parent)
    return out

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    words = " ".join(m["content"] for m in body["messages"]).split()
    n_out, hashes = int(body.get("max_tokens", 32)), block_hashes(words)
    hit = 0
    while hit < len(hashes) and hashes[hit] in CACHE: hit += 1   # walk from block 0; stop at the first miss
    QUERIES.inc(len(words)); HITS.inc(hit * BLOCK)
    for h in hashes:                                          # store the blocks, evicting the least recently used
        CACHE.pop(h, None); CACHE[h] = None
        if len(CACHE) > CACHE_BLOCKS: CACHE.popitem(last=False)
    need = len(words) + n_out
    IN_FLIGHT[0] += need; WAITING.inc()
    async with SLOT:                                          # waits here while all slots are busy
        WAITING.dec(); RUNNING.inc()
        await asyncio.sleep(((len(words) - hit * BLOCK) * PREFILL_MS + n_out * DECODE_MS) / 1000)
        RUNNING.dec(); IN_FLIGHT[0] -= need
    SUCCESS.inc()
    return {"id": f"sim-{NAME}", "object": "chat.completion", "model": body.get("model"), "replica": NAME,
            "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant", "content": f"[SIMULATED replica {NAME}: no model ran]"}}],
            "usage": {"prompt_tokens": len(words), "completion_tokens": n_out, "total_tokens": need,
                      "prompt_tokens_details": {"cached_tokens": hit * BLOCK}}}

@app.get("/metrics")
def metrics():
    KV_USE.set(min(1.0, (IN_FLIGHT[0] + len(CACHE) * BLOCK) / KV_CAPACITY))
    return PlainTextResponse(generate_latest(REG).decode(), media_type="text/plain")

@app.post("/sim/reset")                                       # simulation only: empty the cache between runs
def reset():
    CACHE.clear(); return {"cache_blocks": 0}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
