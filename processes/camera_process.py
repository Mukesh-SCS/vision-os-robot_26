"""Camera producer process."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from hardware.camera import Camera
from utils.logger import get_logger, process_started_message

LOGGER = get_logger(__name__)

try:
    import cv2  # type: ignore

    HAS_CV2 = True
except Exception:  # pragma: no cover
    cv2 = None
    HAS_CV2 = False


def _put_queue_latest(q: Queue, item) -> None:
    """Keep only the newest item (bounded live stream)."""
    try:
        q.put_nowait(item)
    except queue.Full:
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        try:
            q.put_nowait(item)
        except queue.Full:
            pass


def camera_process(frame_queue: Queue, preview_queue: Queue, stop_event: Event) -> None:
    LOGGER.info(process_started_message())
    camera = Camera()
    if not camera.init_camera():
        LOGGER.warning("camera_process running without camera input.")
        while not stop_event.is_set():
            time.sleep(0.5)
        return

    try:
        while not stop_event.is_set():
            frame = camera.read_frame()
            if frame is None:
                time.sleep(settings.CAMERA_POLL_INTERVAL_SEC)
                continue
            if HAS_CV2:
                assert cv2 is not None
                frame = cv2.resize(frame, (settings.FRAME_WIDTH, settings.FRAME_HEIGHT))
                preview = cv2.resize(frame, (settings.PREVIEW_WIDTH, settings.PREVIEW_HEIGHT))
                _put_queue_latest(preview_queue, preview)

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
