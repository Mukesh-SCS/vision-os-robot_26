"""Lightweight timing utilities for reporting and logs."""

from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from statistics import mean
from time import perf_counter
from typing import Dict, List


@dataclass
class MetricSnapshot:
    count: int
    avg_ms: float
    max_ms: float


class TimingCollector:
    """Collects named timing durations in milliseconds."""

    def __init__(self) -> None:
        self._data: Dict[str, List[float]] = defaultdict(list)

    @contextmanager
    def measure(self, name: str):
        start = perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (perf_counter() - start) * 1000.0
            self._data[name].append(elapsed_ms)

    def add(self, name: str, elapsed_ms: float) -> None:
        self._data[name].append(elapsed_ms)

    def snapshot(self) -> Dict[str, MetricSnapshot]:
        result: Dict[str, MetricSnapshot] = {}
        for metric, values in self._data.items():
            if not values:
                continue
            result[metric] = MetricSnapshot(
                count=len(values),
                avg_ms=mean(values),
                max_ms=max(values),
            )
        return result
