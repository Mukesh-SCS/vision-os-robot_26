"""Independent left/right motor channel validation."""

from __future__ import annotations

import time

from hardware.motor_driver import MotorDriver
from utils.logger import configure_logging, get_logger


def _run_step(driver: MotorDriver, logger, label: str, action, duration: float = 1.2) -> None:
    logger.info("Step: %s", label)
    action()
    time.sleep(duration)
    driver.stop()
    time.sleep(0.4)


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    driver = MotorDriver()
    driver.initialize()

    logger.info("Starting independent motor channel test sequence")
    try:
        while True:
            _run_step(driver, logger, "left forward", driver.left_forward)
            _run_step(driver, logger, "left backward", driver.left_backward)
            _run_step(driver, logger, "right forward", driver.right_forward)
            _run_step(driver, logger, "right backward", driver.right_backward)
            _run_step(driver, logger, "both forward", driver.forward, duration=1.5)
            logger.info("Test sequence completed, restarting...")
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    finally:
        driver.stop()
        driver.cleanup()
        logger.info("Motor channel test complete")


if __name__ == "__main__":
    main()
