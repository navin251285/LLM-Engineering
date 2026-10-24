import random
from locust import HttpUser, task

random.seed(27)
PROMPT = "Brightside policy: " + " ".join(f"Rule {i} covers refunds, delivery and warranty claims." for i in range(1, 25))

class Desk(HttpUser):                             # one support agent: wait, ask, wait for the whole answer, repeat
    def wait_time(self):
        return random.expovariate(1 / 8)          # mean 8 s between questions
    @task
    def ask(self):
        self.client.post("/v1/completions", name="completions", json={"model": "brightside-qwen-0.5b",
            "prompt": PROMPT, "max_tokens": random.randint(24, 72), "temperature": 0})
