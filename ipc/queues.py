"""Shared IPC objects for multiprocessing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import Event, Queue

from config import settings


@dataclass
class IPCObjects:
    frame_queue: Queue
    preview_queue: Queue
    vision_result_queue: Queue
    distance_queue: Queue
    decision_queue: Queue
    audio_queue: Queue
    status_queue: Queue
    stop_event: Event


def create_ipc_objects() -> IPCObjects:
    return IPCObjects(
        frame_queue=Queue(maxsize=settings.FRAME_QUEUE_SIZE),
        preview_queue=Queue(maxsize=1),
        vision_result_queue=Queue(maxsize=5),
        distance_queue=Queue(maxsize=5),
        decision_queue=Queue(maxsize=10),
        audio_queue=Queue(maxsize=10),
        status_queue=Queue(maxsize=100),
        stop_event=Event(),
    )
