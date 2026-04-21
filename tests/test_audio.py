"""Manual hardware test for the audio wrapper."""

from __future__ import annotations

import logging
import time

from hardware.audio import Audio

PIN = 25
DURATION_SECONDS = 2
FREQUENCY_HZ = 1000
DUTY_CYCLE = 50


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _build_audio() -> Audio:
    constructor_attempts = (
        {"pin": PIN},
        {"gpio_pin": PIN},
        {},
    )

    for kwargs in constructor_attempts:
        try:
            return Audio(**kwargs)
        except TypeError:
            continue

    try:
        return Audio(PIN)
    except TypeError as exc:
        raise TypeError("Unable to construct hardware.audio.Audio for manual test") from exc


def _start_tone(audio: Audio) -> None:
    if hasattr(audio, "play_tone"):
        try:
            audio.play_tone(FREQUENCY_HZ, DUTY_CYCLE)
        except TypeError:
            audio.play_tone(FREQUENCY_HZ)
        return

    if hasattr(audio, "tone"):
        try:
            audio.tone(FREQUENCY_HZ, DUTY_CYCLE)
        except TypeError:
            audio.tone(FREQUENCY_HZ)
        return

    if hasattr(audio, "start"):
        try:
            audio.start(FREQUENCY_HZ, DUTY_CYCLE)
        except TypeError:
            try:
                audio.start(FREQUENCY_HZ)
            except TypeError:
                audio.start()
        return

    if hasattr(audio, "beep"):
        try:
            audio.beep(FREQUENCY_HZ, DURATION_SECONDS)
        except TypeError:
            audio.beep()
        return

    raise AttributeError("hardware.audio.Audio does not expose a known tone playback method")


def _stop_audio(audio: Audio) -> None:
    for method_name in ("stop", "off", "cleanup", "close"):
        method = getattr(audio, method_name, None)
        if callable(method):
            method()
            return


def main() -> None:
    configure_logging()

    audio = _build_audio()
    logging.info("Starting manual audio test")

    try:
        _start_tone(audio)
        time.sleep(DURATION_SECONDS)
    finally:
        _stop_audio(audio)
        logging.info("Finished manual audio test")
if __name__ == "__main__":
    main()