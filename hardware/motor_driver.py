"""L298N motor driver wrapper."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class MotorPins:
    in1: int = settings.MOTOR_IN1
    in2: int = settings.MOTOR_IN2
    in3: int = settings.MOTOR_IN3
    in4: int = settings.MOTOR_IN4
    ena: int = settings.MOTOR_ENA
    enb: int = settings.MOTOR_ENB


class MotorDriver:
    """Motor actions only; no decision logic."""

    def __init__(self, pins: Optional[MotorPins] = None) -> None:
        self.pins = pins or MotorPins()
        self._pwm_a = None
        self._pwm_b = None
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        if not HAS_GPIO:
            LOGGER.warning("RPi.GPIO unavailable; running motor driver in dry-run mode.")
            self._initialized = True
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (self.pins.in1, self.pins.in2, self.pins.in3, self.pins.in4, self.pins.ena, self.pins.enb):
            GPIO.setup(pin, GPIO.OUT)

        self._pwm_a = GPIO.PWM(self.pins.ena, settings.MOTOR_PWM_FREQUENCY_HZ)
        self._pwm_b = GPIO.PWM(self.pins.enb, settings.MOTOR_PWM_FREQUENCY_HZ)
        self._pwm_a.start(settings.MOTOR_DEFAULT_SPEED)
        self._pwm_b.start(settings.MOTOR_DEFAULT_SPEED)
        self._initialized = True
        LOGGER.info("MotorDriver initialized.")

    def _set(self, in1: bool, in2: bool, in3: bool, in4: bool) -> None:
        self.initialize()
        if not HAS_GPIO:
            LOGGER.info("DRY-RUN motor pins set: %s", (in1, in2, in3, in4))
            return

        GPIO.output(self.pins.in1, GPIO.HIGH if in1 else GPIO.LOW)
        GPIO.output(self.pins.in2, GPIO.HIGH if in2 else GPIO.LOW)
        GPIO.output(self.pins.in3, GPIO.HIGH if in3 else GPIO.LOW)
        GPIO.output(self.pins.in4, GPIO.HIGH if in4 else GPIO.LOW)

    def forward(self) -> None:
        self._set(True, False, True, False)
        LOGGER.debug("motor action = FORWARD")

    def backward(self) -> None:
        self._set(False, True, False, True)
        LOGGER.debug("motor action = BACKWARD")

    def left(self) -> None:
        self._set(False, True, True, False)
        LOGGER.debug("motor action = LEFT")

    def right(self) -> None:
        self._set(True, False, False, True)
        LOGGER.debug("motor action = RIGHT")

    def stop(self) -> None:
        self._set(False, False, False, False)
        LOGGER.debug("motor action = STOP")

    def cleanup(self) -> None:
        if not self._initialized:
            return
        if HAS_GPIO:
            try:
                if self._pwm_a is not None:
                    self._pwm_a.stop()
                if self._pwm_b is not None:
                    self._pwm_b.stop()
                GPIO.cleanup()
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Motor cleanup warning: %s", exc)
        self._initialized = False
