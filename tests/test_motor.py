"""Manual motor test script."""

from __future__ import annotations

import time

from hardware.motor_driver import MotorDriver
from utils.logger import configure_logging, get_logger


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    driver = MotorDriver()

    try:
        logger.info("Testing forward")
        driver.forward()
        time.sleep(1.5)

        logger.info("Testing backward")
        driver.backward()
        time.sleep(1.5)

        logger.info("Testing left")
        driver.left()
        time.sleep(1.0)

        logger.info("Testing right")
        driver.right()
        time.sleep(1.0)
    finally:
        driver.stop()
        driver.cleanup()
        logger.info("Motor test complete")


if __name__ == "__main__":
    main()
