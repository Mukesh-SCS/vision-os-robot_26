"""Camera producer process."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

import cv2

from config import settings
from hardware.camera import Camera
from utils.logger import get_logger, process_started_message

LOGGER = get_logger(__name__)


def camera_process(frame_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    camera = Camera()
    if not camera.init_camera():
        LOGGER.error("camera_process exiting: camera init failed.")
        stop_event.set()
        return

    try:
        while not stop_event.is_set():
            frame = camera.read_frame()
            if frame is None:
                time.sleep(settings.CAMERA_POLL_INTERVAL_SEC)
                continue
            frame = cv2.resize(frame, (settings.FRAME_WIDTH, settings.FRAME_HEIGHT))

            try:
                frame_queue.put_nowait(frame)
            except queue.Full:
                try:
                    frame_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    frame_queue.put_nowait(frame)
                except queue.Full:
                    pass

            time.sleep(settings.CAMERA_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("camera_process failure: %s", exc)
        stop_event.set()
    finally:
        camera.release_camera()
