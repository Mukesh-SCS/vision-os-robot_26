"""Helpers for publishing process status events to GUI."""

from __future__ import annotations

import queue
from multiprocessing import Queue
from typing import Any, Dict


def publish_status(status_queue: Queue, **payload: Any) -> None:
    """Best-effort status enqueue that never blocks worker loops."""
    try:
        status_queue.put_nowait(payload)
    except queue.Full:
        try:
            status_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            status_queue.put_nowait(payload)
        except queue.Full:
            pass
