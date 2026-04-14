"""Manual camera test script."""

from __future__ import annotations

import cv2

from hardware.camera import Camera
from utils.logger import configure_logging, get_logger


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    cam = Camera()
    if not cam.init_camera():
        logger.error("Unable to start camera.")
        return

    try:
        while True:
            frame = cam.read_frame()
            if frame is None:
                continue
            cv2.imshow("Camera Test", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("s"):
                cv2.imwrite("snapshot.jpg", frame)
                logger.info("Saved snapshot.jpg")
            if key == ord("q"):
                break
    finally:
        cam.release_camera()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
