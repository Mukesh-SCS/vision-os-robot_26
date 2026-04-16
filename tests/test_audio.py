import RPi.GPIO as GPIO
import time

PIN = 25


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN, GPIO.OUT)

    pwm = GPIO.PWM(PIN, 1000)  # 1 kHz tone
    pwm.start(50)

    time.sleep(2)

    pwm.stop()
    GPIO.cleanup()


if __name__ == "__main__":
    main()