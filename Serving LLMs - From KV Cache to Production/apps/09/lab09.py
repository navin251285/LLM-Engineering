"""Docker helpers for lesson 09: start the pinned vLLM CPU server, wait until healthy, stop it.

The notebook imports this module so its cells show the measurement, not the container plumbing.
"""
import os, shutil, socket, subprocess, time, atexit
from pathlib import Path
import httpx


def docker_ready():
    """True when the docker command exists and the daemon answers."""
    return (shutil.which("docker") is not None
            and subprocess.run(["docker", "info"], capture_output=True).returncode == 0)


def server_up(base):
    """True when the server answers /health with 200."""
    try:
        return httpx.get(f"{base}/health", timeout=2).status_code == 200
    except httpx.TransportError:
        return False


def start_server(name, image, port, args, key=""):
    """Start the container in the background. The key is passed by name, never on the command line."""
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)   # clear a container left by an interrupted run
    if socket.socket().connect_ex(("127.0.0.1", port)) == 0:
        raise RuntimeError(f"port {port} is busy: stop the other process first")
    run_env, key_flag = dict(os.environ), []
    if key:
        run_env["VLLM_API_KEY"] = key
        key_flag = ["-e", "VLLM_API_KEY"]
    cmd = ["docker", "run", "-d", "--name", name, "-p", f"{port}:8000", "--shm-size", "4g",
           "-v", f"{Path.home() / '.cache' / 'huggingface'}:/root/.cache/huggingface", *key_flag, image, *args]
    started = subprocess.run(cmd, capture_output=True, text=True, env=run_env, timeout=120)
    if started.returncode != 0:
        raise RuntimeError("docker run failed: " + started.stderr[-300:])
    atexit.register(stop_server, name)


def wait_healthy(name, base, polls=240):
    """Poll /health every 2 s (480 s at most). Stop early if the container dies."""
    for _ in range(polls):
        if server_up(base):
            return
        state = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", name],
                               capture_output=True, text=True).stdout.strip()
        if state != "true":
            logs = subprocess.run(["docker", "logs", "--tail", "20", name], capture_output=True, text=True)
            raise RuntimeError("server container stopped:\n" + (logs.stdout + logs.stderr)[-800:])
        time.sleep(2)
    raise TimeoutError("server not healthy after 480 s")


def save_logs_and_stop(name, path):
    """Keep the last 200 log lines in the lesson's data folder, then remove the container."""
    logs = subprocess.run(["docker", "logs", "--tail", "200", name], capture_output=True, text=True)
    Path(path).write_text((logs.stdout + logs.stderr)[-4000:])
    stop_server(name)


def stop_server(name):
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)


# The prompts for the measurement: four Brightside support questions and the policy they are answered under.
QUESTIONS = ["Can I return an opened item?", "How long do refunds take?",
             "Do you ship outside the country?", "Can I change my delivery address?"]
SYSTEM = ("You are the Brightside support desk. Answer in one short sentence. Policy: items can be "
          "returned within 30 days with a receipt. Refunds reach the card within 5 business days.")
