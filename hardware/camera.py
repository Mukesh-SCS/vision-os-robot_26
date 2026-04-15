"""Camera capture wrapper."""

from __future__ import annotations

from typing import Optional

from config import settings
from utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import cv2  # type: ignore

    HAS_CV2 = True
except Exception:  # pragma: no cover
    cv2 = None
    HAS_CV2 = False


class Camera:
    def __init__(self, index: int = settings.CAMERA_INDEX):
        self.index = index
        self.cap: Optional[object] = None

    def init_camera(self) -> bool:
        if not HAS_CV2:
            LOGGER.error("OpenCV (cv2) is not installed; camera is unavailable.")
            return False
        if self.cap is not None and self.cap.isOpened():
            return True
        assert cv2 is not None
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            LOGGER.error("Failed to open camera index %s", self.index)
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        LOGGER.info("Camera initialized at index %s", self.index)
        return True

    def read_frame(self):
        if self.cap is None and not self.init_camera():
            return None
        assert self.cap is not None
        ok, frame = self.cap.read()
        if not ok:
            LOGGER.warning("Camera frame read failed.")
            return None
        return frame

    def release_camera(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            LOGGER.info("Camera released.")
