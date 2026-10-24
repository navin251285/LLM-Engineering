"""SIMULATED replica for lesson 29: an OpenAI-style chat endpoint that takes time but runs no model.
It has SLOTS decode slots like the lab server; an answer takes max_tokens x MS_PER_TOKEN milliseconds."""
import asyncio, sys, time
from fastapi import FastAPI, Request
import uvicorn

NAME, PORT, MS_PER_TOKEN, SLOTS = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
app = FastAPI()
slots = asyncio.Semaphore(SLOTS)
state = {"served": 0, "in_flight": 0}

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    n = int(body.get("max_tokens", 48))
    state["in_flight"] += 1
    try:
        async with slots:                                  # a request waits here while all slots are busy
            await asyncio.sleep(n * MS_PER_TOKEN / 1000)
            state["served"] += 1
    finally:
        state["in_flight"] -= 1
    return {"id": "sim", "object": "chat.completion", "created": int(time.time()), "model": body.get("model"),
            "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant",
                         "content": f"[simulated replica {NAME}: no model ran]"}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": n, "total_tokens": n}}

@app.get("/stats")
def stats():
    return {"replica": NAME, **state}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
