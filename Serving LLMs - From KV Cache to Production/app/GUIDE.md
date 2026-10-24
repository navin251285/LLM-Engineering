# Brightside support desk: the app, step by step

The course builds one app next to the notebooks. Each step adds to it after a chapter, and this
guide shows what changed, why, and how to run it. Work from the course folder
(`topics/kv-forge-15h`) and use its virtual environment, `.venv`.

## Step 1: Ask one question
**After chapter 1 · uses lessons 01–09 (the engine is the server from lesson 08)** — the app answers one support question through the local engine, with a health check and a page with a text box.

### What you add
- `app/pyproject.toml`: the package (`brightside-desk`), its dependencies (FastAPI, uvicorn, the OpenAI SDK) and the test extra (pytest, vcrpy).
- `app/src/brightside_desk/config.py`: the settings, read from the course's `.env` through `tut_env.py`. Nothing secret is typed into the code.
- `app/src/brightside_desk/engine.py`: one call to the engine through the OpenAI SDK, with the Brightside policy as the system message (the same call as lesson 08, step 3).
- `app/src/brightside_desk/api.py`: the FastAPI app. `GET /health`, `POST /ask`, and `GET /` (the page). Engine errors become clear HTTP errors (503 when the engine does not answer).
- `app/src/brightside_desk/static/index.html`: the one-page UI, plain HTML and JavaScript with `fetch`.
- `app/src/brightside_desk/__main__.py`: `python -m brightside_desk` starts the app on the port from `.env`.
- `app/tests/`: four offline tests. The engine's answer is replayed from `tests/cassettes/test_step1_ask.yaml`.
- `llm_replay.py` (course folder): the course's replay helper, copied from `shared/`, so the test recording works like the lessons' recordings.
- `app/README.md`: what the app is and how to run it.

### The code that matters
The engine call is the lesson 08 call, with `base_url` taken from `.env` (lesson 08, step 3 and the OpenAI-compatible server idea):
```python
resp = client.chat.completions.create(
    model=settings.model,
    messages=[{"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": question}],
    max_tokens=settings.max_tokens, temperature=0)
```
Settings come from the environment, so the same code works with any engine (lesson 08, the key stays in `.env`):
```python
vllm_base_url=env("VLLM_BASE_URL", "http://localhost:8000/v1"),
vllm_api_key=env("VLLM_API_KEY", ""),
```
A down engine is a clear answer, not a crash (lesson 08, what a client should expect):
```python
except APIConnectionError:
    raise HTTPException(503, "The engine is not answering. Start it, then ask again (see app/GUIDE.md).")
```
The test replays the engine's answer, so it runs offline (see `tests/test_step1_ask.py`):
```python
llm_replay.start("test_step1_ask")   # recorded once, replayed offline
r = TestClient(create_app(settings=settings)).post("/ask", json={"question": QUESTION})
llm_replay.stop()
```

### Run it
Start the engine first, from the lesson 08 setup (Docker running, the vLLM CPU image, port 8000 in `.env`). Its first answer takes minutes on a CPU, so give it a moment (lesson 08, step 2b). Then, in another terminal:

```bash
cd topics/kv-forge-15h
.venv/bin/python -m pip install -e "app[test]"
cd app/src
../../.venv/bin/uvicorn brightside_desk.api:app --reload --port 8980
```

Open <http://127.0.0.1:8980/> in a browser. Type "Can I return an opened item?" and press Ask.

### Test it
```bash
cd topics/kv-forge-15h/app
../.venv/bin/python -m pytest -q
```

### What you should see
The health check and the page, from the running app:
```text
$ curl http://127.0.0.1:8980/health
{"status":"ok","version":"0.1.0"}
$ curl -o /dev/null -w '%{http_code} %{content_type}\n' http://127.0.0.1:8980/
200 text/html; charset=utf-8
```
A question, through the engine (the answer is the engine's own reply, with the policy's 30 days):
```text
$ curl -X POST http://127.0.0.1:8980/ask -H 'Content-Type: application/json' \
    -d '{"question":"Can I return an opened item?"}'
{"answer":"Yes, you can return an opened item within 30 days of receiving it with a valid receipt.","model":"brightside-qwen-0.5b","prompt_tokens":68,"completion_tokens":22}
```
In the browser you see the status line "Service is up (version 0.1.0).", the text box, and the answer under the Ask button. If the engine is not running, the answer area shows "The engine is not answering. Start it, then ask again (see app/GUIDE.md)."

The tests:
```text
$ ../.venv/bin/python -m pytest -q
....                                                                     [100%]
4 passed in 2.50s
```

## Step 2: Tuned and measured
**After chapter 3 · uses lessons 07, 08, 16 and 18 (the checkpoint's TTFT target) on the engine of lessons 16 and 18** — the app streams each answer from the engine, measures the first-token time and the time per token at the client, keeps the engine's settings in the config, and shows the latency so far.

### What you add
- `app/src/brightside_desk/config.py`: four more settings, read from `.env` with the values the lessons tuned: the engine's length limit (`BRIGHTSIDE_MAX_MODEL_LEN`, 2048 from lesson 16), the two targets (`BRIGHTSIDE_SLO_TTFT_S` 2.0 from lesson 18, `BRIGHTSIDE_SLO_TPOT_MS` 15 from lesson 07) and the size of the stats window.
- `app/src/brightside_desk/metrics.py` (new): the timing split (first token, last token, mean gap after the first), the percentiles, and the rolling summary that counts an answer only when it meets both targets.
- `app/src/brightside_desk/engine.py`: `ask` now streams the answer and records the arrival time of each token.
- `app/src/brightside_desk/api.py`: `/ask` returns `ttft_ms`, `tpot_ms` and `total_ms`; new `GET /settings` (the tuned values, never the key or the engine address) and `GET /stats` (p50 and p95, and the share within the targets). The version is now 0.2.0.
- `app/src/brightside_desk/static/index.html`: the answer shows its timing, and a "Latency so far" panel reads `/stats`.
- `app/tests/test_step2_tuned.py` (new): nine offline tests for the settings, the timing split, the SLO count, the window, the 503 counter and one streamed answer replayed from `tests/cassettes/test_step2_ask_stream.yaml`.
- `app/tests/cassettes/test_step1_ask.yaml` is re-recorded, because `/ask` now streams. The step 1 test still passes unchanged.

### The code that matters
The answer is streamed, so the clock runs at the client, from the send to each token (lesson 07, lesson 08 step 4):
```python
stream = client.chat.completions.create(model=settings.model, messages=[...], max_tokens=settings.max_tokens,
                                        temperature=0, stream=True, stream_options={"include_usage": True})
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        arrivals.append(time.perf_counter() - t_send)
```
The three clocks come from the arrival times. TPOT is the mean gap after the first token, as lesson 07 defines it, and a one-token answer has no gap (`metrics.py`):
```python
ttft, last = arrivals_s[0], arrivals_s[-1]
tpot = (last - ttft) / (n_tokens - 1) if n_tokens >= 2 else None
```
An answer counts toward the targets only when it meets both, which is lesson 07's goodput idea applied to one service (`metrics.py`):
```python
def meets_slo(self, timing: Timing) -> bool:
    if timing.ttft_ms / 1000 > self.slo_ttft_s:
        return False
    return timing.tpot_ms is None or timing.tpot_ms <= self.slo_tpot_ms
```

### Run it
The engine must be running with the flags that lesson 16 tuned (the lab's Docker setup, port 8000 in `.env`). Its first answer on a CPU takes several minutes, so send one question to it before you open the app (lesson 18, step 3). Then, in another terminal:

```bash
cd topics/kv-forge-15h
docker run -d --name tut-kv-forge-15h-app2 -p 8000:8000 --shm-size 4g \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface" vllm/vllm-openai-cpu:v0.32.0 \
  Qwen/Qwen2.5-0.5B-Instruct --served-model-name brightside-qwen-0.5b --host 0.0.0.0 \
  --dtype float32 --enforce-eager --max-model-len 2048 --max-num-seqs 4 \
  --max-num-batched-tokens 2048 --kv-cache-memory-bytes 2147483648
.venv/bin/python -m pip install -e "app[test]"
cd app/src
../../.venv/bin/uvicorn brightside_desk.api:app --reload --port 8980
```

Open <http://127.0.0.1:8980/>, ask a question, and read the timing under the answer. The engine's settings and the targets are shown under "Latency so far".

### Test it
```bash
cd topics/kv-forge-15h/app
../.venv/bin/python -m pytest -q
```
The step 2 tests alone: `../.venv/bin/python -m pytest -q tests/test_step2_tuned.py`. They run offline, so you can stop the engine first.

### What you should see
The health check now reports the new version, and the settings are the tuned values from `.env` (the key and the address are not shown):
```text
$ curl http://127.0.0.1:8980/health
{"status":"ok","version":"0.2.0"}
$ curl http://127.0.0.1:8980/settings
{"model":"brightside-qwen-0.5b","max_tokens":60,"max_model_len":2048,"timeout_s":300.0,"slo":{"ttft_s":2.0,"tpot_ms":15.0}}
```
One question, streamed from the engine, with its timing:
```text
$ curl -X POST http://127.0.0.1:8980/ask -H 'Content-Type: application/json' \
    -d '{"question":"Can I return an opened item?"}'
{"answer":"Yes, you can return an opened item within 30 days of receiving it with a valid receipt.","model":"brightside-qwen-0.5b","prompt_tokens":68,"completion_tokens":22,"ttft_ms":1398.4,"tpot_ms":204.5,"total_ms":5693.9}
$ curl http://127.0.0.1:8980/stats
{"answers":1,"errors":0,"ttft_ms_p50":1398.4,"ttft_ms_p95":1398.4,"tpot_ms_p50":204.5,"tpot_ms_p95":204.5,"within_slo":0.0}
```
The first token came in 1.4 s, inside the 2.0 s target from lesson 18. The time per token was 205 ms, far above the 15 ms example from lesson 07, so `within_slo` is 0. That is the measured result on this 4-core CPU, not a bug: the lab machine has no GPU. Lesson 27 shows how to measure a deployment against its SLO before you change a flag.

The tests:
```text
$ ../.venv/bin/python -m pytest -q
.............                                                            [100%]
13 passed in 2.51s
```
