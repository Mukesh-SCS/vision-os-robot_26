"""Simple PWM speaker output on GPIO 25."""

from __future__ import annotations

import time

from config import settings
from utils.logger import get_logger

LOGGER = get_logger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore
    HAS_GPIO = True
except Exception:
    GPIO = None
    HAS_GPIO = False


class Audio:
    def __init__(self, pin: int = settings.AUDIO_PIN):
        self.pin = pin
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return

        if not HAS_GPIO:
            LOGGER.warning("GPIO unavailable; audio running in dry mode.")
            self._initialized = True
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self._initialized = True
        LOGGER.info("Audio initialized on pin %s", self.pin)

    def tone(self, frequency: int = 1000, duration: float = 0.2, duty: float = 50.0) -> None:
        self.initialize()

        if not HAS_GPIO:
            LOGGER.info("DRY-RUN tone: freq=%s duration=%s", frequency, duration)
            return

        try:
            safe_duty = float(duty)
        except (TypeError, ValueError):
            safe_duty = 50.0
        safe_duty = max(0.0, min(100.0, safe_duty))

        pwm = None
        try:
            pwm = GPIO.PWM(self.pin, frequency)
            pwm.start(safe_duty)
            time.sleep(duration)
        finally:
            if pwm is not None:
                try:
                    pwm.stop()
                except Exception as exc:
                    LOGGER.warning("Audio PWM stop warning: %s", exc)
                finally:
                    pwm = None

            try:
                GPIO.output(self.pin, GPIO.LOW)
            except Exception:
                pass

    def beep(self) -> None:
        self.tone(frequency=1000, duration=0.2)

    def alert(self) -> None:
        for _ in range(3):
            self.tone(frequency=1200, duration=0.15)
            time.sleep(0.08)

    def cleanup(self) -> None:
        if HAS_GPIO and self._initialized:
            try:
                GPIO.output(self.pin, GPIO.LOW)
                GPIO.cleanup(self.pin)
            except Exception as exc:
                LOGGER.warning("Audio cleanup warning: %s", exc)

        self._initialized = False