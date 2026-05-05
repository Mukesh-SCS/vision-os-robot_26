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
    idle_since = None
    last_change_at = 0.0
    last_status_emit = 0.0

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
                idle_since = None
            except queue.Empty:
                command = None
                if idle_since is None:
                    idle_since = time.monotonic()

            now = time.monotonic()
            if command and command in command_map and command != last_command:
                hold_elapsed = now - last_change_at
                if hold_elapsed >= settings.MOTOR_COMMAND_HOLD_SEC:
                    if command != "STOP":
                        # Briefly boost both channels to overcome wheel stiction on starts.
                        driver.set_side_speed(
                            settings.MOTOR_START_BOOST_DUTY,
                            settings.MOTOR_START_BOOST_DUTY,
                        )
                        time.sleep(settings.MOTOR_START_BOOST_SEC)
                        driver.set_side_speed(
                            settings.MOTOR_DEFAULT_SPEED + settings.MOTOR_LEFT_TRIM,
                            settings.MOTOR_DEFAULT_SPEED + settings.MOTOR_RIGHT_TRIM,
                        )
                    command_map[command]()
                    last_command = command
                    last_change_at = now
                    LOGGER.info("motor command executed: %s", command)
                    publish_status(status_queue, source="motor", motor_state=command)

            if (
                idle_since is not None
                and last_command != "STOP"
                and (now - idle_since) >= settings.MOTOR_IDLE_STOP_SEC
            ):
                driver.stop()
                last_command = "STOP"
                last_change_at = now
                publish_status(status_queue, source="motor", motor_state="STOP")
            elif (now - last_status_emit) >= 0.5:
                publish_status(status_queue, source="motor", motor_state=last_command or "IDLE")
                last_status_emit = now

            time.sleep(settings.MOTOR_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("motor_process failure: %s", exc)
        stop_event.set()
    finally:
        try:
            driver.stop()
        finally:
            driver.cleanup()
