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
    """Motor control wrapper for L298N."""

    def __init__(self, pins: Optional[MotorPins] = None) -> None:
        self.pins = pins or MotorPins()
        self._pwm_a = None
        self._pwm_b = None
        self._initialized = False
        self._left_speed = settings.MOTOR_DEFAULT_SPEED + settings.MOTOR_LEFT_TRIM
        self._right_speed = settings.MOTOR_DEFAULT_SPEED + settings.MOTOR_RIGHT_TRIM

    def initialize(self) -> None:
        if self._initialized:
            return

        if not HAS_GPIO:
            LOGGER.warning("RPi.GPIO unavailable; running motor driver in dry-run mode.")
            self._initialized = True
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in (
            self.pins.in1,
            self.pins.in2,
            self.pins.in3,
            self.pins.in4,
            self.pins.ena,
            self.pins.enb,
        ):
            GPIO.setup(pin, GPIO.OUT)

        GPIO.output(self.pins.in1, GPIO.LOW)
        GPIO.output(self.pins.in2, GPIO.LOW)
        GPIO.output(self.pins.in3, GPIO.LOW)
        GPIO.output(self.pins.in4, GPIO.LOW)

        self._pwm_a = GPIO.PWM(self.pins.ena, settings.MOTOR_PWM_FREQUENCY_HZ)
        self._pwm_b = GPIO.PWM(self.pins.enb, settings.MOTOR_PWM_FREQUENCY_HZ)

        self._pwm_a.start(self._clamp_duty(self._left_speed))
        self._pwm_b.start(self._clamp_duty(self._right_speed))

        self._initialized = True
        LOGGER.info("MotorDriver initialized.")

    @staticmethod
    def _clamp_duty(duty_cycle: float) -> float:
        return max(0.0, min(100.0, float(duty_cycle)))

    def _apply_side(
        self,
        *,
        left_forward: bool,
        right_forward: bool,
        left_enabled: bool = True,
        right_enabled: bool = True,
    ) -> None:
        self.initialize()
        left_invert = bool(settings.LEFT_MOTOR_INVERT)
        right_invert = bool(settings.RIGHT_MOTOR_INVERT)

        if not left_enabled:
            in1, in2 = False, False
        else:
            left_dir = left_forward if not left_invert else not left_forward
            in1, in2 = left_dir, not left_dir

        if not right_enabled:
            in3, in4 = False, False
        else:
            right_dir = right_forward if not right_invert else not right_forward
            in3, in4 = right_dir, not right_dir

        self._set(in1, in2, in3, in4)

    def _set(self, in1: bool, in2: bool, in3: bool, in4: bool) -> None:
        self.initialize()

        if not HAS_GPIO:
            LOGGER.info("DRY-RUN motor pins set: %s", (in1, in2, in3, in4))
            return

        GPIO.output(self.pins.in1, GPIO.HIGH if in1 else GPIO.LOW)
        GPIO.output(self.pins.in2, GPIO.HIGH if in2 else GPIO.LOW)
        GPIO.output(self.pins.in3, GPIO.HIGH if in3 else GPIO.LOW)
        GPIO.output(self.pins.in4, GPIO.HIGH if in4 else GPIO.LOW)

    def set_speed(self, duty_cycle: float) -> None:
        self.initialize()
        self.set_side_speed(duty_cycle, duty_cycle)

    def set_side_speed(self, left_duty_cycle: float, right_duty_cycle: float) -> None:
        self.initialize()

        if not HAS_GPIO:
            LOGGER.info("DRY-RUN speed set L=%.1f%% R=%.1f%%", left_duty_cycle, right_duty_cycle)
            return

        left_duty = self._clamp_duty(left_duty_cycle + settings.MOTOR_LEFT_TRIM)
        right_duty = self._clamp_duty(right_duty_cycle + settings.MOTOR_RIGHT_TRIM)

        if self._pwm_a is not None:
            self._pwm_a.ChangeDutyCycle(left_duty)
        if self._pwm_b is not None:
            self._pwm_b.ChangeDutyCycle(right_duty)

    def forward(self) -> None:
        self._apply_side(left_forward=True, right_forward=True)
        LOGGER.debug("motor action = FORWARD")

    def backward(self) -> None:
        self._apply_side(left_forward=False, right_forward=False)
        LOGGER.debug("motor action = BACKWARD")

    def left(self) -> None:
        self._apply_side(left_forward=False, right_forward=True)
        LOGGER.debug("motor action = LEFT")

    def right(self) -> None:
        self._apply_side(left_forward=True, right_forward=False)
        LOGGER.debug("motor action = RIGHT")

    def left_forward(self) -> None:
        self._apply_side(left_forward=True, right_forward=True, right_enabled=False)
        LOGGER.debug("motor action = LEFT_FORWARD")

    def left_backward(self) -> None:
        self._apply_side(left_forward=False, right_forward=True, right_enabled=False)
        LOGGER.debug("motor action = LEFT_BACKWARD")

    def right_forward(self) -> None:
        self._apply_side(left_forward=True, right_forward=True, left_enabled=False)
        LOGGER.debug("motor action = RIGHT_FORWARD")

    def right_backward(self) -> None:
        self._apply_side(left_forward=True, right_forward=False, left_enabled=False)
        LOGGER.debug("motor action = RIGHT_BACKWARD")

    def stop(self) -> None:
        self._set(False, False, False, False)
        LOGGER.debug("motor action = STOP")

    def cleanup(self) -> None:
        if not self._initialized:
            return

        if HAS_GPIO:
            try:
                GPIO.output(self.pins.in1, GPIO.LOW)
                GPIO.output(self.pins.in2, GPIO.LOW)
                GPIO.output(self.pins.in3, GPIO.LOW)
                GPIO.output(self.pins.in4, GPIO.LOW)

                if self._pwm_a is not None:
                    try:
                        self._pwm_a.stop()
                    except Exception as exc:
                        LOGGER.warning("PWM A stop warning: %s", exc)
                    finally:
                        self._pwm_a = None

                if self._pwm_b is not None:
                    try:
                        self._pwm_b.stop()
                    except Exception as exc:
                        LOGGER.warning("PWM B stop warning: %s", exc)
                    finally:
                        self._pwm_b = None

                GPIO.cleanup(
                    (
                        self.pins.in1,
                        self.pins.in2,
                        self.pins.in3,
                        self.pins.in4,
                        self.pins.ena,
                        self.pins.enb,
                    )
                )
            except Exception as exc:
                LOGGER.warning("Motor cleanup warning: %s", exc)

        self._initialized = False