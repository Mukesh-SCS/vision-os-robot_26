"""Decision logic process combining vision + ultrasonic signals."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from utils.logger import get_logger, process_started_message
from utils.status import publish_status

LOGGER = get_logger(__name__)


def _derive_motion_command(vision_state: str, distance_payload: dict) -> str:
    distance = distance_payload.get("distance_cm")
    danger = bool(distance_payload.get("danger"))
    if danger or (distance is not None and distance < settings.OBSTACLE_THRESHOLD_CM):
        return "STOP"
    if vision_state == "OBSTACLE_LEFT":
        return "RIGHT"
    if vision_state == "OBSTACLE_RIGHT":
        return "LEFT"
    if vision_state == "STOP":
        return "STOP"
    return "FORWARD"


def decision_process(
    vision_result_queue: Queue,
    distance_queue: Queue,
    decision_queue: Queue,
    status_queue: Queue,
    stop_event: Event,
) -> None:
    LOGGER.info(process_started_message())
    latest_vision = "CLEAR"
    latest_distance = {"distance_cm": None, "danger": False}

    try:
        while not stop_event.is_set():
            try:
                latest_vision = vision_result_queue.get_nowait()
            except queue.Empty:
                pass

            try:
                latest_distance = distance_queue.get_nowait()
            except queue.Empty:
                pass

            command = _derive_motion_command(latest_vision, latest_distance)
            publish_status(
                status_queue,
                source="decision",
                command=command,
                vision=latest_vision,
                distance_cm=latest_distance.get("distance_cm"),
            )
            try:
                decision_queue.put_nowait(command)
            except queue.Full:
                try:
                    decision_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    decision_queue.put_nowait(command)
                except queue.Full:
                    pass

            LOGGER.debug(
                "decision=%s (vision=%s distance=%s)",
                command,
                latest_vision,
                latest_distance.get("distance_cm"),
            )
            time.sleep(settings.DECISION_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("decision_process failure: %s", exc)
        stop_event.set()
