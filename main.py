"""Entry point for the autonomous robot multiprocessing system."""

from __future__ import annotations

import multiprocessing as mp
import time

from ipc.queues import create_ipc_objects
from processes.audio_process import audio_process
from processes.camera_process import camera_process
from processes.decision_process import decision_process
from processes.motor_process import motor_process
from processes.ultrasonic_process import ultrasonic_process
from processes.vision_process import vision_process
from ui.dashboard import RobotDashboard
from utils.logger import configure_logging, get_logger


def _spawn_processes(ipc):
    return [
        mp.Process(
            name="UltrasonicProcess",
            target=ultrasonic_process,
            args=(ipc.distance_queue, ipc.audio_queue, ipc.status_queue, ipc.stop_event),
        ),
        mp.Process(
            name="CameraProcess",
            target=camera_process,
            args=(ipc.frame_queue, ipc.preview_queue, ipc.stop_event),
        ),
        mp.Process(
            name="VisionProcess",
            target=vision_process,
            args=(ipc.frame_queue, ipc.vision_result_queue, ipc.status_queue, ipc.stop_event),
        ),
        mp.Process(
            name="DecisionProcess",
            target=decision_process,
            args=(ipc.vision_result_queue, ipc.distance_queue, ipc.decision_queue, ipc.status_queue, ipc.stop_event),
        ),
        mp.Process(name="MotorProcess", target=motor_process, args=(ipc.decision_queue, ipc.status_queue, ipc.stop_event)),
        mp.Process(name="AudioProcess", target=audio_process, args=(ipc.audio_queue, ipc.stop_event)),
    ]


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    ipc = create_ipc_objects()
    processes = _spawn_processes(ipc)

    logger.info("Starting robot OS processes...")
    for proc in processes:
        proc.start()
        logger.info("Started %s (pid=%s)", proc.name, proc.pid)
        time.sleep(0.05)

    try:
        process_names = [proc.name for proc in processes]
        dashboard = RobotDashboard(ipc.status_queue, ipc.preview_queue, ipc.stop_event, process_names)
        dashboard.run()
    except Exception as exc:
        logger.warning("GUI unavailable (%s). Falling back to headless mode.", exc)
        while True:
            if ipc.stop_event.is_set():
                logger.warning("Stop event received from child process.")
                break
            if any(not proc.is_alive() for proc in processes):
                dead = [proc.name for proc in processes if not proc.is_alive()]
                logger.warning("One or more child processes exited: %s", dead)
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping...")
    finally:
        ipc.stop_event.set()
        logger.info("Stopping child processes...")
        for proc in processes:
            proc.join(timeout=2.0)
            if proc.is_alive():
                logger.warning("Terminating unresponsive process %s", proc.name)
                proc.terminate()
                proc.join(timeout=1.0)

        logger.info("Shutdown complete.")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
