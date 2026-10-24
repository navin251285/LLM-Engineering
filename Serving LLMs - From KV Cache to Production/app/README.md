# Brightside support desk

A small FastAPI service that answers support questions with a model served by your local
vLLM engine, and a one-page web UI to ask them in the browser. It is the app the course
builds chapter by chapter; see [GUIDE.md](GUIDE.md) for the step-by-step build.

## What it is
- `GET /health` says the service is up.
- `POST /ask` takes `{"question": "..."}` and returns the engine's answer, streamed from the engine,
  with its latency: time to the first token, time per output token, and the total time.
- `GET /settings` shows the tuned settings the app runs with and the targets it is judged against.
- `GET /stats` summarises the most recent answers: p50 and p95 of the first-token and per-token times,
  and the share that meets both targets.
- `GET /` serves the page: a text box, an Ask button, the answer with its timing, and the latency so far.

The engine is any OpenAI-compatible server. Lesson 08 starts one in Docker (vLLM, CPU image,
port 8000 in `.env`), with the flags that lesson 16 tuned. The app never starts the engine itself.

## Run it
From the course folder, with the topic's virtual environment:

```bash
cd app/src
../../.venv/bin/uvicorn brightside_desk.api:app --reload --port 8980
```

Then open <http://127.0.0.1:8980/>.

## Settings
Read from the course's `.env` (through `tut_env.py`), never typed into the code:
`VLLM_BASE_URL` (the engine, ends in `/v1`), `VLLM_API_KEY` (only if the engine has a key).
Optional, with the defaults the course uses:
`BRIGHTSIDE_MODEL` (brightside-qwen-0.5b), `BRIGHTSIDE_TIMEOUT_S` (300), `BRIGHTSIDE_MAX_TOKENS` (60),
`BRIGHTSIDE_MAX_MODEL_LEN` (2048, the engine's `--max-model-len`), `BRIGHTSIDE_SLO_TTFT_S` (2.0),
`BRIGHTSIDE_SLO_TPOT_MS` (15), `BRIGHTSIDE_STATS_WINDOW` (200), `BRIGHTSIDE_PORT` (8980).

## Tests
```bash
cd app
../.venv/bin/python -m pytest -q
```
The tests run offline: the engine's streamed answers are replayed from `tests/cassettes/` (recorded once
with `llm_replay`), so no engine or key is needed. The timing and SLO functions are tested directly.
