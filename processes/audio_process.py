"""Optional audio alert process."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from hardware.audio import Audio
from utils.logger import get_logger, process_started_message
from utils.status import publish_status

LOGGER = get_logger(__name__)


def audio_process(audio_queue: Queue, status_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    audio = Audio(pin=settings.AUDIO_PIN)
    audio.initialize()
    last_beep_time = 0.0
    status_event = "IDLE"
    last_status_emit = 0.0

    try:
        while not stop_event.is_set():
            now = time.perf_counter()
            try:
                msg = audio_queue.get(timeout=settings.QUEUE_GET_TIMEOUT_SEC)
            except queue.Empty:
                # Keep BEEP visible briefly so dashboard updates can observe it.
                if status_event == "BEEP" and (now - last_beep_time) >= max(
                    settings.BEEP_DURATION_SEC,
                    settings.AUDIO_POLL_INTERVAL_SEC * 2,
                ):
                    status_event = "IDLE"
                if (now - last_status_emit) >= 0.2:
                    publish_status(status_queue, source="audio", audio_state=status_event)
                    last_status_emit = now
                time.sleep(settings.AUDIO_POLL_INTERVAL_SEC)
                continue

            event = msg.get("event") if isinstance(msg, dict) else msg
            if event == "BEEP" and (now - last_beep_time) >= settings.BEEP_COOLDOWN_SEC:
                audio.tone(
                    frequency=settings.BEEP_FREQUENCY_HZ,
                    duration=settings.BEEP_DURATION_SEC,
                    duty=50.0,
                )
                last_beep_time = now
                status_event = "BEEP"
                publish_status(status_queue, source="audio", audio_state="BEEP")
                last_status_emit = now
    except Exception as exc:
        LOGGER.exception("audio_process failure: %s", exc)
        stop_event.set()
    finally:
        try:
            audio.cleanup()
        except Exception:
            pass
