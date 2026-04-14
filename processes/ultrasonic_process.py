"""Ultrasonic polling process."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from hardware.ultrasonic import UltrasonicSensor
from utils.logger import get_logger, process_started_message
from utils.status import publish_status

LOGGER = get_logger(__name__)


def ultrasonic_process(distance_queue: Queue, audio_queue: Queue, status_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    sensor = UltrasonicSensor()

    try:
        while not stop_event.is_set():
            distance = sensor.get_distance()
            danger = distance is not None and distance < settings.OBSTACLE_THRESHOLD_CM
            payload = {"distance_cm": distance, "danger": danger}

            try:
                distance_queue.put_nowait(payload)
            except queue.Full:
                try:
                    distance_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    distance_queue.put_nowait(payload)
                except queue.Full:
                    pass

            if danger:
                try:
                    audio_queue.put_nowait("BEEP")
                except queue.Full:
                    pass

            publish_status(
                status_queue,
                source="ultrasonic",
                distance_cm=distance,
                danger=danger,
            )

            LOGGER.debug("distance=%s cm danger=%s", distance, danger)
            time.sleep(settings.ULTRASONIC_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("ultrasonic_process failure: %s", exc)
        stop_event.set()
    finally:
        sensor.cleanup()
