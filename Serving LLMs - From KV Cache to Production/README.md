# KV Forge: Mastering LLM Inference, from KV Cache to Production

KV Forge is a 15-hour course on serving large language models. You start with one question:
why does serving a model cost more and fail differently than running a web API? From there you
work out the KV cache size from a model's config, tune an engine to a latency target, size replicas
and cost per million tokens from a QPS target, run a small serving service with routing, autoscaling
and an eval gate, and write up the design. The running example is the Brightside support desk: a
team answers support questions with a shared 1,500-token policy prompt, and the course turns that
into real capacity numbers. Every lesson runs on a laptop; the parts that need Docker, a GPU or a
cloud account are marked and have a recorded result when you do not have them.

**Full syllabus (PDF):** [SYLLABUS.pdf](SYLLABUS.pdf) · **Glossary:** [GLOSSARY.md](GLOSSARY.md)
· **Build the app step by step:** [app/GUIDE.md](app/GUIDE.md) and [app/README.md](app/README.md)

## Who it is for

Developers and platform engineers who run Python services and need to size, tune, operate and
justify LLM serving. No GPU background is assumed. You will know what you have learned when you can:

- derive KV cache size and a concurrency limit from a model config and a memory budget;
- tune an engine to a TTFT target and justify each flag with a measured number;
- turn a QPS target into a concurrency number, a replica count and cost per million tokens;
- run a serving service with a gateway, autoscaling and a rollout gate, and defend the design in writing.

## Prerequisites

- **Python 3.12** with `venv` (the course uses Python 3.12 for every lesson).
- **Basic Python**: functions, classes, dictionaries, reading a JSON file, running a script.
- **Some HTTP**: what a request and a response are; a JSON body.
- **Docker with the Compose plugin** for the lessons that start a local cluster (08, 09, 16, 18, 27,
  30, 31, 33, 35, 37). Without Docker, those lessons show their recorded output, labelled as such.
- Optional: a GPU, or a Google Cloud project with GPU quota, for the real GPU runs in lessons 20, 21 and 27.
  Without them, the course uses recorded results.
- Internet access the first time, to download packages and a model in a few lessons (08, 18).

No API key is needed to run the course.

## Setup

Work from the course folder, `topics/kv-forge-15h`.

### 1. Create the virtual environment

```bash
cd topics/kv-forge-15h
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

The packages are listed in [requirements.txt](requirements.txt) with the versions the course was
built and tested with (see [Installed versions](#installed-versions)). Install them only in this
virtual environment; never globally.

### 2. Register the kernel

```bash
.venv/bin/python -m ipykernel install --user --name tut-kv-forge-15h --display-name "KV Forge (tut-kv-forge-15h)"
```

The notebooks select the kernel `tut-kv-forge-15h`. If you do not see it in Jupyter, run the command
again and restart Jupyter.

### 3. Set up `.env` (optional settings)

```bash
cp .env.example .env
```

Open `.env` and fill in only the values you need. Every value is optional: a lesson that does not
find its value uses a local fallback or its recorded result. Keep `.env` on your own machine: do not
commit it, and do not paste its values into notebooks, issues or screenshots.

| Name | What it is for | Used by |
| --- | --- | --- |
| `VLLM_BASE_URL` | address of the serving endpoint (the Compose cluster or a local vLLM server) | the lessons that call an engine, from lesson 08, and the app |
| `VLLM_API_KEY` | key for an OpenAI-compatible server started with `--api-key`; leave empty for a local server | lessons 15 and 16, and the app |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project for the optional GPU VM runs | lessons 20, 21 and 27 (optional) |
| `GCP_GPU_ZONE` | zone with L4 quota for the optional GPU VM | lessons 20, 21 and 27 (optional) |
| `GCS_RESULTS_BUCKET` | bucket where the optional GPU VM runs save their results | lessons 20, 21 and 27 (optional) |

Leave the three Google Cloud values unset to use the recorded GPU results. Lessons read values with
`from tut_env import env; env("NAME")`, so nothing is typed into the code.

## How to run it

Start Jupyter from the course folder with the course's environment:

```bash
cd topics/kv-forge-15h
.venv/bin/python -m jupyter notebook
```

Open `notebooks/`, and choose the kernel **KV Forge (tut-kv-forge-15h)**. Run the notebooks in order,
from `01` to `40`; each one says what it builds on.

**VS Code:** open the `topics/kv-forge-15h` folder, select `.venv` as the Python interpreter, then open a
notebook and pick the kernel **KV Forge (tut-kv-forge-15h)**.

Each lesson has a **Try it** with its answer in a hidden cell tagged `solution`. Try the exercise
first, then open the answer to compare.

## What `TUT_ENABLE` does

By default, a cell tagged for something your machine does not have is **skipped**, and the notebook
says so. `TUT_ENABLE` turns those cells on for one run. It is an environment variable holding a
comma-separated list, set when you start Jupyter:

| Tag | Turned on by | Example cells |
| --- | --- | --- |
| `needs-docker` | `TUT_ENABLE=docker` | start the Compose cluster |
| `needs-download` | `TUT_ENABLE=download` | download a model |
| `needs-gpu` | `TUT_ENABLE=gpu` | real GPU runs (lessons 20, 21) |
| `slow` | `TUT_ENABLE=slow` | load tests that take more than about a minute (lesson 27) |
| `needs-llm` | `TUT_ENABLE=llm` | calls to a paid model (none in this course: its LLM calls are replayed) |

For example, to run the Docker lessons on this machine:

```bash
TUT_ENABLE=docker .venv/bin/python -m jupyter notebook
```

`TUT_ENABLE=all` turns on every tag. The skipped cells are never silently faked: a skipped cell
either shows its recorded output, labelled as recorded, or tells you what to re-run with `TUT_ENABLE`.

## Setting up Docker and Kubernetes

Some lessons run a real multi-node Docker Compose cluster on one machine. The setup guide is in `SETUP_CLUSTERS.md`. Check what your machine can run with:

```bash
python3 check_env.py
```

Without Docker, those cells are skipped and show output recorded from a real run.

## Lessons

Level is the level of the chapter the lesson sits in. Priority: **core** lessons are the Essentials
path; **professional** and **deep** lessons add depth. "Needs" lists what the lesson uses beyond the
laptop; with nothing listed, it runs on the laptop alone.

| ID | Title | Level | Priority | Needs |
| --- | --- | --- | --- | --- |
| 01 | Why LLM inference is its own problem | L1 | core | none |
| 02 | Decoding one token at a time | L1 | core | none |
| 03 | KV cache size from a model config | L1 | core | none |
| 04 | Attention variants: MHA, MQA, GQA and MLA | L1 | professional | none |
| 05 | Max concurrency from the memory budget | L1 | core | none |
| 06 | Prefill, decode and the roofline | L1 | core | none |
| 07 | Measuring TTFT, TPOT and goodput | L1 | core | none |
| 08 | Serve a model and call it: the API and streaming | L1 | core | Docker, download |
| 09 | Checkpoint: capacity report for one model | L1 | core | Docker |
| 10 | Why paged memory: reserving the maximum wastes the GPU | L3 | core | none |
| 11 | PagedAttention and the block allocator | L3 | core | none |
| 12 | Continuous batching and chunked prefill | L3 | core | none |
| 13 | Preemption and offload | L3 | core | none |
| 14 | Prefix caching: hashes, radix trees and hit rate | L3 | core | none |
| 15 | Choosing a serving engine | L3 | core | none |
| 16 | The vLLM flags you will tune | L3 | core | Docker |
| 17 | Speculative decoding and multi-LoRA | L3 | core | none |
| 18 | Checkpoint: tune an engine to a TTFT target | L3 | core | Docker, download |
| 19 | Why parallelism: a 70B model does not fit one GPU | L4 | core | none |
| 20 | Weight quantization: INT8, FP8, AWQ and GGUF | L4 | core | GPU (optional) |
| 21 | KV cache quantization and measuring quality loss | L4 | core | GPU (optional) |
| 22 | Tensor parallelism and all-reduce | L4 | core | none |
| 23 | Pipeline and expert parallelism; sizing a 70B model | L4 | core | none |
| 24 | GPU memory hierarchy and picking the cheapest GPU | L4 | core | none |
| 25 | Checkpoint: pick a GPU and parallelism for an SLO | L4 | core | none |
| 26 | Little's law: from QPS to concurrency | L5 | core | none |
| 27 | Load tests that match reality | L5 | core | Docker, slow |
| 28 | Cost per million tokens and build vs buy | L5 | core | none |
| 29 | Why a gateway: one endpoint, many replicas | L5 | core | none |
| 30 | Routing: prefix-aware and KV-aware balancing | L5 | core | Docker |
| 31 | Autoscaling on queue depth, not GPU utilisation | L5 | core | Docker |
| 32 | Deploying the server: containers, config and GPU scheduling | L5 | core | none (kubeconform optional) |
| 33 | Reliability drill: OOM, node loss and the dashboard | L5 | core | Docker |
| 34 | Disaggregated prefill and multi-node serving | L5 | core | none |
| 35 | Rollouts with eval gates | L5 | core | Docker |
| 36 | Security and tenancy for an LLM endpoint | L5 | core | none |
| 37 | Checkpoint: operate the mock cluster | L5 | core | Docker |
| 38 | Scale maths: 10x, 100x and HA/DR | L6 | deep | none |
| 39 | Platform patterns, frontier and case studies | L6 | deep | none |
| 40 | Capstone: design the Llama 70B serving platform | L6 | core | none |

The checkpoint and project lessons (09, 18, 25, 28, 37 and 40) each end with a deliverable you can
keep: a capacity report, a tuned engine, a hardware choice, a build-vs-buy case, a running cluster check
and the capstone design.

## The course app: Brightside support desk service

Alongside the notebooks, the course builds a small app in [app/](app/): a FastAPI backend and a
one-page web UI, run with one command. The notebooks stay complete on their own; the app grows one
step after each chapter, and [app/GUIDE.md](app/GUIDE.md) explains each step.

| Step | After chapter | Level | What it adds | Status |
| --- | --- | --- | --- | --- |
| 1 | 1 | Basic | **Ask one question**: a `/ask` endpoint served by the local engine, a page with a text box, a health check | built |
| 2 | 3 | Intermediate | **Tuned and measured**: engine settings from the config, latency metrics, tests | built |
| 3 | 5 | Advanced | **Replicas and a gateway**: two local uvicorn processes behind a small gateway (no Docker in the app), queue metrics, admission control | not built yet |
| 4 | 6 | Advanced | **Finish and run it** (final): one run command, full tests, README | not built yet |

To run the app as it stands (steps 1 and 2), start the engine first (lesson 08 shows how), then:

```bash
cd topics/kv-forge-15h/app/src
../../.venv/bin/uvicorn brightside_desk.api:app --reload --port 8980
```

Open <http://127.0.0.1:8980/> in a browser. Check it with `curl http://127.0.0.1:8980/health`.
The app reads `VLLM_BASE_URL` and `VLLM_API_KEY` from `.env` and never starts the engine itself.
Its tests run offline, from recorded answers:

```bash
cd topics/kv-forge-15h/app
../.venv/bin/python -m pytest -q
```

## Time box and levels

The course is one course of **at most 15 hours**, from the first definition to the most advanced
practice. The lessons add up to about 15 hours (895 minutes of lesson time, 10 to 35 minutes each).

| Level | Chapters | Lessons | Time | Share of the course |
| --- | --- | --- | --- | --- |
| Basic | 1 · Foundations and one server | 01–09 | about 3 h 20 min | 22% |
| Intermediate | 2 · Memory, batching and engines; 3 · Quantization, parallelism and hardware | 10–25 | about 6 h | 40% |
| Advanced | 4 · Capacity and economics; 5 · Serving at scale and operations; 6 · Enterprise and the capstone | 26–40 | about 5 h 35 min | 37% |

Each level takes at least 15% of the time. You can stop after Basic with a working capacity model, or
after Intermediate with a tuned and quantized engine, and come back for Advanced later.

Shorter paths through the same course: **Essentials** (the core lessons only, 37 lessons, about 14 h)
and **Professional** (38 lessons, about 14 h). The **Complete** course is all 40 lessons.

## Where next

Roles, disciplines and technologies this course leads to. Maturity says how settled each one is.

- **Inference performance engineer** (role, established): makes model serving faster and cheaper per
  token, from engine internals to kernels and profiling. Start it:
  `/tutorial "Inference performance engineering" basic reuse:kv-forge-15h`
- **ML platform and inference SRE** (role, established): runs model serving as a service, with SLOs,
  capacity, GPU fleets and incident response. Start it:
  `/tutorial "ML platform reliability" basic reuse:kv-forge-15h`
- **Distributed inference on Kubernetes** (technology, growing): prefix-aware routing, prefill and
  decode disaggregation and tiered KV cache, as Kubernetes-native stacks. Start it:
  `/tutorial "Distributed inference on Kubernetes" basic reuse:kv-forge-15h`

Go deeper, when you need it: CUDA graphs, attention backends and FlashAttention (see the vLLM docs);
custom GPU kernels (a separate course); sparsity and distillation; reading the vLLM scheduler source
after lesson 13; Dynamo and llm-d after lesson 34; RoPE, NTK scaling and YaRN.

## Installed versions

These are the requirements in [requirements.txt](requirements.txt). `pip` installs the newest release
that meets each one, so your versions may be a little newer; the constraints in brackets are the ones
that matter for the course.

| Package | Requirement |
| --- | --- |
| numpy | `==2.5.3` (llmcompressor 0.14.0 needs `<=2.5.3`, lesson 20) |
| pydantic | `>=2.14.1` |
| python-dotenv | `>=1.2.4` |
| fastapi | `>=0.150.0` |
| uvicorn | `>=0.54.0` |
| httpx | `>=0.28.1` |
| openai | `>=2.20.0,<3.0.0` (litellm in lesson 29 needs `openai<3`) |
| prometheus-client | `>=0.21.0` |
| locust | `>=2.46.7` |
| pytest | `>=9.1.1` |
| ipykernel | `>=7.4.0` |
| nbformat | any |
| nbclient | any |
| reportlab | any |
| pypdf | `>=6.21.1` |
| python-pptx | any |
| llmcompressor | `>=0.14.0` |
| torch | `>=2.7` |
| transformers | `>=5.0` |
| safetensors | `>=0.4` |
| guidellm | `>=0.8.1` |
| litellm[proxy] | `>=1.106.2` |
| pyyaml | `>=6.0` |

The serving engines (vLLM, SGLang) and llama.cpp or Ollama run in Docker or on a GPU VM, not in this
virtual environment. Their versions are pinned in the lesson that starts them. Python: 3.12.

## Troubleshooting

**`kubeconform` is not on your PATH (lesson 32).** Steps 4 and 5 check a Kubernetes manifest offline
with `kubeconform`. If it is not installed, the lesson prints the recorded output from
`data/recorded/32.json` and says so. Nothing else changes: the lesson does not deploy to a cluster.
To run the check yourself, install `kubeconform` and make sure it is on your PATH, then re-run the cell.

**Docker is not running, or the Compose plugin is missing.** Lessons that need Docker are skipped, or
show their recorded output, when Docker does not answer. Start Docker, check that `docker compose version`
prints a version, then re-run with `TUT_ENABLE=docker` set.

**The first engine start takes minutes.** On a CPU image, vLLM takes 1 to 3 minutes on a 4-core machine
the first time, longer when the model is not yet cached (lesson 08). Wait for the health check to pass;
the lessons poll it with a timeout rather than a fixed sleep.

**The engine is not answering in the app.** The app returns HTTP 503 with "The engine is not answering".
Start the engine, check `VLLM_BASE_URL` in `.env` (it ends in `/v1`), then ask again.

**The kernel `tut-kv-forge-15h` is not listed.** Run the kernel command from the Setup section again,
then restart Jupyter.

**Port 8980 is in use.** Start the app on another port with `--port`, or set `BRIGHTSIDE_PORT` in `.env`.

**A GPU lesson says "recorded".** Lessons 20, 21 and 27 make real GPU runs only when you enable them
(`TUT_ENABLE=gpu`) and have the optional Google Cloud settings. Otherwise the lesson shows the recorded
results and labels them as such.
