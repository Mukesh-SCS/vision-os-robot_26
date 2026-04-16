"""Camera capture wrapper preferring Raspberry Pi Picamera2 with OpenCV fallback."""

from __future__ import annotations

from typing import Optional

from config import settings
from utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import cv2  # type: ignore
    HAS_CV2 = True
except Exception:
    cv2 = None
    HAS_CV2 = False

try:
    from picamera2 import Picamera2  # type: ignore
    HAS_PICAMERA2 = True
except Exception:
    Picamera2 = None
    HAS_PICAMERA2 = False


class Camera:
    def __init__(self, index: int = settings.CAMERA_INDEX):
        self.index = index
        self.cap: Optional[object] = None
        self.picam2: Optional[object] = None
        self.backend = None

    def init_camera(self) -> bool:
        if self.backend is not None:
            return True

        if HAS_PICAMERA2:
            try:
                self.picam2 = Picamera2()
                config = self.picam2.create_preview_configuration(
                    main={"size": (settings.FRAME_WIDTH, settings.FRAME_HEIGHT), "format": "RGB888"}
                )
                self.picam2.configure(config)
                self.picam2.start()
                self.backend = "picamera2"
                LOGGER.info("Camera initialized with Picamera2.")
                return True
            except Exception as exc:
                LOGGER.warning("Picamera2 init failed, falling back to OpenCV: %s", exc)
                self.picam2 = None

        if HAS_CV2:
            try:
                self.cap = cv2.VideoCapture(self.index)
                if not self.cap.isOpened():
                    LOGGER.error("Failed to open camera index %s with OpenCV", self.index)
                    return False
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
                self.backend = "opencv"
                LOGGER.info("Camera initialized with OpenCV at index %s", self.index)
                return True
            except Exception as exc:
                LOGGER.error("OpenCV camera init failed: %s", exc)
                self.cap = None

        LOGGER.error("No usable camera backend found.")
        return False

    def read_frame(self):
        if self.backend is None and not self.init_camera():
            return None

        if self.backend == "picamera2" and self.picam2 is not None:
            try:
                frame = self.picam2.capture_array()
                if HAS_CV2 and cv2 is not None:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return frame
            except Exception as exc:
                LOGGER.warning("Picamera2 frame read failed: %s", exc)
                return None

        if self.backend == "opencv" and self.cap is not None:
            ok, frame = self.cap.read()
            if not ok:
                LOGGER.warning("OpenCV camera frame read failed.")
                return None
            return frame

        return None

    def release_camera(self) -> None:
        try:
            if self.picam2 is not None:
                self.picam2.stop()
                self.picam2 = None
            if self.cap is not None:
                self.cap.release()
                self.cap = None
        finally:
            self.backend = None
            LOGGER.info("Camera released.")