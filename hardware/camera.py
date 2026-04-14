"""Camera capture wrapper."""

from __future__ import annotations

from typing import Optional

import cv2

from config import settings
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class Camera:
    def __init__(self, index: int = settings.CAMERA_INDEX):
        self.index = index
        self.cap: Optional[cv2.VideoCapture] = None

    def init_camera(self) -> bool:
        if self.cap is not None and self.cap.isOpened():
            return True
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
