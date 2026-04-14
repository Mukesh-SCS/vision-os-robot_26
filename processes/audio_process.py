"""Optional audio alert process."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from utils.logger import get_logger, process_started_message

LOGGER = get_logger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore

    HAS_GPIO = True
except Exception:  # pragma: no cover
    GPIO = None
    HAS_GPIO = False


def _setup_buzzer():
    if not HAS_GPIO:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(settings.AUDIO_PIN, GPIO.OUT)
    GPIO.output(settings.AUDIO_PIN, GPIO.LOW)


def _beep():
    if not HAS_GPIO:
        LOGGER.info("BEEP (dry-run)")
        return
    GPIO.output(settings.AUDIO_PIN, GPIO.HIGH)
    time.sleep(settings.BEEP_DURATION_SEC)
    GPIO.output(settings.AUDIO_PIN, GPIO.LOW)


def audio_process(audio_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    _setup_buzzer()
    last_beep_time = 0.0

    try:
        while not stop_event.is_set():
            try:
                msg = audio_queue.get(timeout=settings.QUEUE_GET_TIMEOUT_SEC)
            except queue.Empty:
                time.sleep(settings.AUDIO_POLL_INTERVAL_SEC)
                continue

            now = time.perf_counter()
            if msg == "BEEP" and (now - last_beep_time) >= settings.BEEP_COOLDOWN_SEC:
                _beep()
                last_beep_time = now
    except Exception as exc:
        LOGGER.exception("audio_process failure: %s", exc)
        stop_event.set()
    finally:
        if HAS_GPIO:
            try:
                GPIO.output(settings.AUDIO_PIN, GPIO.LOW)
                GPIO.cleanup((settings.AUDIO_PIN,))
            except Exception:
                pass
