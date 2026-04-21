"""Vision analysis process with contour fallback and optional YOLO."""

from __future__ import annotations

import queue
import time
from multiprocessing import Event, Queue

from config import settings
from utils.logger import get_logger, process_started_message
from utils.status import publish_status

LOGGER = get_logger(__name__)

try:
    import cv2  # type: ignore
    import numpy as np

    HAS_VISION_DEPS = True
except Exception:  # pragma: no cover
    cv2 = None
    np = None
    HAS_VISION_DEPS = False

try:
    from ultralytics import YOLO  # type: ignore

    HAS_YOLO = True
except Exception:  # pragma: no cover
    YOLO = None
    HAS_YOLO = False


def _detect_with_contours(frame):
    if not HAS_VISION_DEPS:
        return "CLEAR", 0, frame
    assert cv2 is not None
    assert np is not None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 70, 150)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = frame.shape[:2]
    image_area = float(h * w)
    left_area = 0.0
    right_area = 0.0
    max_area = 0.0
    box_count = 0

    annotated = frame.copy()
    center_x = w // 2
    cv2.line(annotated, (center_x, 0), (center_x, h), (120, 120, 120), 1)

    for c in contours:
        area = float(cv2.contourArea(c))
        if area < settings.VISION_MIN_CONTOUR_AREA:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        cx = x + (bw // 2)
        max_area = max(max_area, area)
        box_count += 1

        if cx < center_x:
            left_area += area
        else:
            right_area += area

        cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 255, 255), 2)

    if max_area >= image_area * settings.VISION_STOP_AREA_RATIO:
        state = "STOP"
    else:
        area_delta = left_area - right_area
        deadzone = image_area * settings.VISION_BOX_CENTER_DEADZONE * 0.1
        if area_delta > deadzone:
            state = "OBSTACLE_LEFT"
        elif area_delta < -deadzone:
            state = "OBSTACLE_RIGHT"
        else:
            state = "CLEAR"

    cv2.putText(
        annotated,
        f"{state} boxes={box_count}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0) if state == "CLEAR" else (0, 165, 255),
        2,
    )
    return state, box_count, annotated


def _detect_with_yolo(frame, model):
    assert cv2 is not None
    h, w = frame.shape[:2]
    image_area = float(h * w)
    results = model.predict(
        source=frame,
        conf=settings.YOLO_CONFIDENCE,
        imgsz=settings.YOLO_IMAGE_SIZE,
        verbose=False,
    )
    r = results[0]
    annotated = frame.copy()
    boxes = getattr(r, "boxes", None)
    box_count = 0
    left_area = 0.0
    right_area = 0.0
    max_area = 0.0
    center_x = w // 2
    cv2.line(annotated, (center_x, 0), (center_x, h), (120, 120, 120), 1)
    if boxes is not None:
        for box in boxes:
            box_count += 1
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            conf = float(box.conf[0].item()) if box.conf is not None else 0.0
            area = float(max(1, (x2 - x1) * (y2 - y1)))
            cx = (x1 + x2) // 2
            max_area = max(max_area, area)
            if cx < center_x:
                left_area += area
            else:
                right_area += area
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 180, 0), 2)
            cv2.putText(annotated, f"{conf:.2f}", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 1)

    if max_area >= image_area * settings.VISION_STOP_AREA_RATIO:
        state = "STOP"
    elif left_area > right_area * 1.2:
        state = "OBSTACLE_LEFT"
    elif right_area > left_area * 1.2:
        state = "OBSTACLE_RIGHT"
    else:
        state = "CLEAR"
    cv2.putText(
        annotated,
        f"{state} boxes={box_count} YOLO",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0) if state == "CLEAR" else (0, 165, 255),
        2,
    )
    return state, box_count, annotated


def vision_process(
    frame_queue: Queue,
    vision_result_queue: Queue,
    status_queue: Queue,
    preview_queue: Queue,
    stop_event: Event,
) -> None:
    LOGGER.info(process_started_message())
    if not HAS_VISION_DEPS:
        LOGGER.warning("OpenCV/NumPy unavailable; vision process using CLEAR fallback.")
    yolo_model = None
    if settings.YOLO_ENABLED:
        if HAS_YOLO:
            try:
                yolo_model = YOLO(settings.YOLO_MODEL_PATH)
                LOGGER.info("YOLO enabled with model: %s", settings.YOLO_MODEL_PATH)
            except Exception as exc:
                LOGGER.warning("Failed to load YOLO model; using contour fallback: %s", exc)
        else:
            LOGGER.warning("YOLO requested but ultralytics not installed; using contour fallback.")
    try:
        while not stop_event.is_set():
            try:
                frame = frame_queue.get(timeout=settings.QUEUE_GET_TIMEOUT_SEC)
            except queue.Empty:
                time.sleep(settings.VISION_POLL_INTERVAL_SEC)
                continue

            if yolo_model is not None:
                state, box_count, annotated = _detect_with_yolo(frame, yolo_model)
            else:
                state, box_count, annotated = _detect_with_contours(frame)

            publish_status(status_queue, source="vision", vision=state, box_count=box_count)
            try:
                vision_result_queue.put_nowait({"state": state, "box_count": box_count})
            except queue.Full:
                try:
                    vision_result_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    vision_result_queue.put_nowait({"state": state, "box_count": box_count})
                except queue.Full:
                    pass
            try:
                preview_queue.put_nowait(annotated)
            except queue.Full:
                try:
                    preview_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    preview_queue.put_nowait(annotated)
                except queue.Full:
                    pass
            time.sleep(settings.VISION_POLL_INTERVAL_SEC)
    except Exception as exc:
        LOGGER.exception("vision_process failure: %s", exc)
        stop_event.set()
