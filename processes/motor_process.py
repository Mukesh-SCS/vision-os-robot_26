"""Motor command consumer process."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from hardware.motor_driver import MotorDriver
from utils.logger import get_logger, process_started_message
from utils.status import publish_status

LOGGER = get_logger(__name__)


def motor_process(decision_queue: Queue, status_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    driver = MotorDriver()
    last_command = None
    idle_ticks = 0

    command_map = {
        "FORWARD": driver.forward,
        "BACKWARD": driver.backward,
        "LEFT": driver.left,
        "RIGHT": driver.right,
        "STOP": driver.stop,
    }

    try:
        while not stop_event.is_set():
            try:
                command = decision_queue.get(timeout=settings.QUEUE_GET_TIMEOUT_SEC)
                idle_ticks = 0
            except queue.Empty:
                command = None
                idle_ticks += 1

            if command and command in command_map and command != last_command:
                command_map[command]()
                last_command = command
                LOGGER.info("motor command executed: %s", command)
                publish_status(status_queue, source="motor", motor_state=command)
            elif idle_ticks > 5 and last_command != "STOP":
                driver.stop()
                last_command = "STOP"
                publish_status(status_queue, source="motor", motor_state="STOP")

            time.sleep(settings.MOTOR_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("motor_process failure: %s", exc)
        stop_event.set()
    finally:
        try:
            driver.stop()
        finally:
            driver.cleanup()
