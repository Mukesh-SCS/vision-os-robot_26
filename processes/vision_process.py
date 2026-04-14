"""Vision analysis process (lightweight CV only)."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

import cv2
import numpy as np

from config import settings
from utils.logger import get_logger, process_started_message

LOGGER = get_logger(__name__)


def _analyze_frame(frame: np.ndarray) -> str:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 80, 160)

    h, w = edges.shape
    roi = edges[h // 2 :, :]
    left_score = int(np.sum(roi[:, : w // 2] > 0))
    right_score = int(np.sum(roi[:, w // 2 :] > 0))
    total_score = left_score + right_score

    if total_score > 15000:
        return "STOP"
    if left_score > right_score * 1.25:
        return "OBSTACLE_LEFT"
    if right_score > left_score * 1.25:
        return "OBSTACLE_RIGHT"
    return "CLEAR"


def vision_process(frame_queue: Queue, vision_result_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    try:
        while not stop_event.is_set():
            try:
                frame = frame_queue.get(timeout=settings.QUEUE_GET_TIMEOUT_SEC)
            except queue.Empty:
                time.sleep(settings.VISION_POLL_INTERVAL_SEC)
                continue

            result = _analyze_frame(frame)
            try:
                vision_result_queue.put_nowait(result)
            except queue.Full:
                try:
                    vision_result_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    vision_result_queue.put_nowait(result)
                except queue.Full:
                    pass
            time.sleep(settings.VISION_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("vision_process failure: %s", exc)
        stop_event.set()
