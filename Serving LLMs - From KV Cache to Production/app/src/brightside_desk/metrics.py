"""Latency metrics for the app: time to first token (TTFT), time per output token (TPOT), and the SLO.

The clock runs at the client, from the request send to each streamed token (lesson 07). These
functions hold no network code, so the tests check them directly.
"""
from __future__ import annotations

import math
import threading
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Timing:
    """One answer's clock: milliseconds to the first token, to the last token, and the mean gap between tokens."""

    ttft_ms: float
    total_ms: float
    tpot_ms: float | None   # None for a one-token answer: there is no gap to average (lesson 07)


def timing_from_arrivals(arrivals_s: list[float], n_tokens: int) -> Timing:
    """Split a streamed answer's arrival times (seconds since the request was sent) into TTFT, total and TPOT.

    TPOT is the mean gap after the first token: (last - first) / (tokens - 1), as in lesson 07.
    """
    if not arrivals_s:
        raise ValueError("no tokens arrived: nothing to time")
    ttft, last = arrivals_s[0], arrivals_s[-1]
    tpot = (last - ttft) / (n_tokens - 1) if n_tokens >= 2 else None
    return Timing(ttft_ms=ttft * 1000, total_ms=last * 1000, tpot_ms=None if tpot is None else tpot * 1000)


def percentile(values: list[float], pct: float) -> float | None:
    """Nearest-rank percentile: the value that pct% of the values stay at or under (None if no values)."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


class LatencyStats:
    """The most recent answers' timings, and how many of them met the targets. Thread-safe."""

    def __init__(self, window: int, slo_ttft_s: float, slo_tpot_ms: float) -> None:
        self._recent: deque[Timing] = deque(maxlen=window)
        self._errors = 0
        self._lock = threading.Lock()
        self.slo_ttft_s = slo_ttft_s
        self.slo_tpot_ms = slo_tpot_ms

    def record(self, timing: Timing) -> None:
        with self._lock:
            self._recent.append(timing)

    def record_error(self) -> None:
        with self._lock:
            self._errors += 1

    def meets_slo(self, timing: Timing) -> bool:
        """An answer counts only if it meets both targets (lesson 07: goodput)."""
        if timing.ttft_ms / 1000 > self.slo_ttft_s:
            return False
        return timing.tpot_ms is None or timing.tpot_ms <= self.slo_tpot_ms

    def summary(self) -> dict:
        with self._lock:
            items = list(self._recent)
            errors = self._errors
        ttft = [t.ttft_ms for t in items]
        tpot = [t.tpot_ms for t in items if t.tpot_ms is not None]
        within = sum(self.meets_slo(t) for t in items)
        return {
            "answers": len(items),
            "errors": errors,
            "ttft_ms_p50": _round(percentile(ttft, 50)),
            "ttft_ms_p95": _round(percentile(ttft, 95)),
            "tpot_ms_p50": _round(percentile(tpot, 50)),
            "tpot_ms_p95": _round(percentile(tpot, 95)),
            "within_slo": round(within / len(items), 3) if items else None,
        }


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 1)
