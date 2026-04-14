"""HC-SR04 ultrasonic distance sensor wrapper."""

from __future__ import annotations

import time
from typing import Optional

from config import settings
from utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore

    HAS_GPIO = True
except Exception:  # pragma: no cover - expected on non-Pi systems
    GPIO = None
    HAS_GPIO = False


class UltrasonicSensor:
    def __init__(self, trig_pin: int = settings.ULTRASONIC_TRIG_PIN, echo_pin: int = settings.ULTRASONIC_ECHO_PIN):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        if not HAS_GPIO:
            LOGGER.warning("RPi.GPIO unavailable; ultrasonic sensor in simulated mode.")
            self._initialized = True
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trig_pin, GPIO.LOW)
        time.sleep(0.05)
        self._initialized = True
        LOGGER.info("UltrasonicSensor initialized.")

    def get_distance(self) -> Optional[float]:
        """Return distance in centimeters or None when invalid/timeout."""
        self.initialize()
        if not HAS_GPIO:
            # Simulated "clear path" value for development machines.
            return 100.0

        timeout = settings.ULTRASONIC_TIMEOUT_SEC
        try:
            GPIO.output(self.trig_pin, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.trig_pin, GPIO.LOW)

            start_wait = time.perf_counter()
            while GPIO.input(self.echo_pin) == 0:
                pulse_start = time.perf_counter()
                if pulse_start - start_wait > timeout:
                    return None

            start_wait = time.perf_counter()
            while GPIO.input(self.echo_pin) == 1:
                pulse_end = time.perf_counter()
                if pulse_end - start_wait > timeout:
                    return None

            duration = pulse_end - pulse_start
            distance_cm = (duration * 34300) / 2
            if distance_cm <= 0 or distance_cm > 500:
                return None
            return round(distance_cm, 2)
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Ultrasonic read failure: %s", exc)
            return None

    def cleanup(self) -> None:
        if HAS_GPIO and self._initialized:
            try:
                GPIO.cleanup((self.trig_pin, self.echo_pin))
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Ultrasonic cleanup warning: %s", exc)
        self._initialized = False
