"""Manual ultrasonic sensor test script."""

from __future__ import annotations

import time

from hardware.ultrasonic import UltrasonicSensor
from utils.logger import configure_logging, get_logger


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    sensor = UltrasonicSensor()

    try:
        while True:
            distance = sensor.get_distance()
            logger.info("distance = %s cm", distance)
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        sensor.cleanup()


if __name__ == "__main__":
    main()
