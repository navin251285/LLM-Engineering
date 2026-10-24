"""SIMULATED fleet for lesson 31: a fluid model, one tick = one simulated minute. It runs NO model.
Arrivals, capacity, KV share and the cold start are parameters of the simulation, not measurements."""
# (requests arriving, requests the KV memory lets run per replica, KV share per running request)
TRACE = [(2, 4, 0.25)] * 5 + [(20, 4, 0.25)] * 8 + [(12, 2, 0.5)] * 20 + [(2, 4, 0.25)] * 5   # short prompts, a burst, long prompts, calm
CAP, SLOTS = 6, 4                       # requests one replica finishes per tick with all 4 decode slots; decode slots
MIN_R, MAX_R = 1, 6                     # replica bounds
COLD = 4                                # ticks (minutes) a new replica needs before it serves. This lesson's own stand-in, deliberately shorter than lesson 27's CPU image (about 10 minutes to the first answer), so the figures are conservative
DOWN_WINDOW = 5                         # scale-down uses the largest desire of the last 5 ticks; mirrors the HPA default of 300 s

def simulate(rule, cold=COLD):
    """rule(signals, replicas) -> desired replicas. Returns one row per simulated minute."""
    replicas, starting, queue, recent, rows = 1, [], 0.0, [], []
    for t, (arrivals, allowed, kv_share) in enumerate(TRACE):
        starting = [p - 1 for p in starting if p > 1]         # ticks left for each replica still loading
        ready = replicas - len(starting)
        demand = queue + arrivals
        running = min(allowed * ready, demand)                # requests holding a decode slot
        queue = demand - min(demand, CAP * ready * allowed / SLOTS)
        signals = {"waiting": queue, "util": running / (SLOTS * ready),   # util = share of decode slots busy (GPU stand-in)
                   "kv": min(1.0, kv_share * running / ready)}
        want = min(MAX_R, max(MIN_R, rule(signals, replicas)))
        recent = (recent + [want])[-DOWN_WINDOW:]
        if want < replicas: want = max(recent)                # scale-down waits for the window
        if want > replicas: starting += [cold] * (want - replicas)
        elif want < replicas: starting = starting[:max(0, len(starting) - (replicas - want))]
        replicas = want
        rows.append({"t": t, "arrivals": arrivals, "queue": round(queue, 1), "util": round(signals["util"], 2),
                     "kv": round(signals["kv"], 2), "replicas": replicas, "ready": replicas - len(starting)})
    return rows
