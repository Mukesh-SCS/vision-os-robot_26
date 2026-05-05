"""Tkinter dashboard for live robot status."""

from __future__ import annotations

import queue
import time
import tkinter as tk
from multiprocessing import Event, Queue
from tkinter import ttk

from config import settings

try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None
    HAS_PIL = False


class RobotDashboard:
    def __init__(
        self,
        status_queue: Queue,
        preview_queue: Queue,
        stop_event: Event,
        process_names: list[str],
    ):
        self.status_queue = status_queue
        self.preview_queue = preview_queue
        self.stop_event = stop_event
        self.process_names = process_names
        self.start_time = time.time()
        self.last_status = {
            "distance_cm": "N/A",
            "danger": "N/A",
            "vision": "N/A",
            "box_count": 0,
            "command": "N/A",
            "motor_state": "N/A",
            "audio_state": "N/A",
        }
        self.process_state = {name: "RUNNING" for name in process_names}
        self._photo_ref = None

        self.root = tk.Tk()
        self.root.title("Vision OS Robot Dashboard")
        self.root.geometry("1100x620")
        self.root.minsize(960, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        ttk.Label(outer, text="Vision OS Robot", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Live status while processes run").pack(anchor="w", pady=(0, 8))

        body = ttk.Frame(outer)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        preview_w = settings.PREVIEW_WIDTH
        preview_h = settings.PREVIEW_HEIGHT

        # Left: live camera (large fixed pixel area)
        cam_frame = ttk.LabelFrame(body, text="Live camera", padding=8)
        cam_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 16))

        self._preview_canvas = tk.Canvas(
            cam_frame,
            width=preview_w,
            height=preview_h,
            bg="#1a1a1a",
            highlightthickness=2,
            highlightbackground="#3d3d3d",
            relief=tk.SUNKEN,
        )
        self._preview_canvas.pack()
        self._preview_placeholder_id = self._preview_canvas.create_text(
            preview_w // 2,
            preview_h // 2,
            text="Waiting for camera…",
            fill="#888888",
            font=("Segoe UI", 11),
            justify=tk.CENTER,
            width=preview_w - 40,
        )
        if not HAS_PIL:
            self._preview_canvas.itemconfig(
                self._preview_placeholder_id,
                text="Install Pillow for preview:\npip install Pillow",
            )

        # Right: status column
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")

        self.uptime_var = tk.StringVar(value="Uptime: 0s")
        ttk.Label(right, textvariable=self.uptime_var).pack(anchor="w", pady=(0, 8))

        self.distance_var = tk.StringVar(value="Distance (cm): N/A")
        self.danger_var = tk.StringVar(value="Danger: N/A")
        self.vision_var = tk.StringVar(value="Vision: N/A")
        self.box_count_var = tk.StringVar(value="Boxes: 0")
        self.command_var = tk.StringVar(value="Decision Command: N/A")
        self.motor_var = tk.StringVar(value="Motor State: N/A")
        self.audio_var = tk.StringVar(value="Audio State: N/A")

        for var in (
            self.distance_var,
            self.danger_var,
            self.vision_var,
            self.box_count_var,
            self.command_var,
            self.motor_var,
            self.audio_var,
        ):
            ttk.Label(right, textvariable=var).pack(anchor="w")

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, pady=10)
        ttk.Label(right, text="Process Health").pack(anchor="w")

        self.proc_var = tk.StringVar(value=self._process_text())
        ttk.Label(right, textvariable=self.proc_var, justify=tk.LEFT).pack(anchor="w", pady=(4, 10))

        ttk.Button(right, text="Stop Robot", command=self._on_close).pack(anchor="w")

    def _process_text(self) -> str:
        return "\n".join(f"- {name}: {state}" for name, state in self.process_state.items())

    def _drain_status_queue(self) -> None:
        while True:
            try:
                payload = self.status_queue.get_nowait()
            except queue.Empty:
                break

            self.last_status.update(payload)

    def _drain_preview_queue(self):
        """Return latest preview frame (numpy BGR) or None."""
        latest = None
        while True:
            try:
                latest = self.preview_queue.get_nowait()
            except queue.Empty:
                break
        return latest

    def _update_preview_image(self, frame) -> None:
        if not HAS_PIL or frame is None:
            return
        try:
            import numpy as np

            arr = np.asarray(frame)
            if arr.ndim != 3 or arr.shape[2] != 3:
                return
            rgb = arr[:, :, ::-1]
            pil_image = Image.fromarray(rgb)
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:  # older Pillow
                resample = Image.LANCZOS
            pil_image = pil_image.resize((settings.PREVIEW_WIDTH, settings.PREVIEW_HEIGHT), resample)
            self._photo_ref = ImageTk.PhotoImage(pil_image)
            self._preview_canvas.delete("all")
            self._preview_placeholder_id = None
            w, h = settings.PREVIEW_WIDTH, settings.PREVIEW_HEIGHT
            self._preview_canvas.create_image(
                w // 2,
                h // 2,
                image=self._photo_ref,
                anchor=tk.CENTER,
            )
        except Exception:
            self._preview_canvas.delete("all")
            self._preview_placeholder_id = self._preview_canvas.create_text(
                settings.PREVIEW_WIDTH // 2,
                settings.PREVIEW_HEIGHT // 2,
                text="Preview error",
                fill="#cc6666",
                font=("Segoe UI", 11),
            )

    def _refresh(self) -> None:
        self._drain_status_queue()
        preview_frame = self._drain_preview_queue()
        if preview_frame is not None:
            self._update_preview_image(preview_frame)

        elapsed = int(time.time() - self.start_time)
        self.uptime_var.set(f"Uptime: {elapsed}s")
        self.distance_var.set(f"Distance (cm): {self.last_status['distance_cm']}")
        self.danger_var.set(f"Danger: {self.last_status['danger']}")
        self.vision_var.set(f"Vision: {self.last_status['vision']}")
        self.box_count_var.set(f"Boxes: {self.last_status['box_count']}")
        self.command_var.set(f"Decision Command: {self.last_status['command']}")
        self.motor_var.set(f"Motor State: {self.last_status['motor_state']}")
        self.audio_var.set(f"Audio State: {self.last_status['audio_state']}")

        if self.stop_event.is_set():
            for key in self.process_state:
                self.process_state[key] = "STOPPING"
        self.proc_var.set(self._process_text())
        self.root.after(66, self._refresh)

    def _on_close(self) -> None:
        self.stop_event.set()
        self.root.after(100, self.root.destroy)

    def run(self) -> None:
        self._refresh()
        self.root.mainloop()
