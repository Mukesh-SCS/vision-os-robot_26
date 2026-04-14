# Vision-Based Autonomous Robot with OS-Level Multi-Process Scheduling

## Overview
This project builds a Raspberry Pi autonomous robot that demonstrates Operating System concepts through a real multi-process control pipeline.

The robot combines:
- camera-based scene analysis
- ultrasonic obstacle safety override
- motor control through L298N
- optional audio alert signaling

Core OS goals shown in code:
- concurrent process execution
- inter-process communication (IPC) via queues
- clear task separation between processes
- safety-first priority behavior (sensor override)

---

## Implemented Architecture
The runtime starts independent worker processes:
- `UltrasonicProcess` (highest conceptual priority)
- `CameraProcess`
- `VisionProcess`
- `DecisionProcess`
- `MotorProcess`
- `AudioProcess` (optional alert)

Data flow:
1. camera captures frames into `frame_queue`
2. vision reads frames and publishes scene states
3. ultrasonic publishes distance + danger flags
4. decision combines vision + distance into motion commands
5. motor executes movement commands
6. audio receives beep triggers on danger

---

## Hardware Requirements
- Raspberry Pi 4/5 with Raspberry Pi OS
- Camera module or USB camera
- HC-SR04 ultrasonic sensor
- L298N motor driver
- 4WD chassis with motors
- battery pack for motors
- jumper wires and common ground
- buzzer/speaker (optional)

---

## Software Requirements
- Python 3.10+ recommended
- `opencv-python`
- `numpy`
- `gpiozero`
- `RPi.GPIO`
- optional on Pi: `picamera2` (install on the Raspberry Pi, not required on Windows)

Install:
```bash
pip install -r requirements.txt
```

---

## Project Structure
```bash
vision-os-robot_26/
├── main.py
├── requirements.txt
├── README.md
├── INSTRUCTION.md
│
├── config/
│   └── settings.py
├── hardware/
│   ├── camera.py
│   ├── motor_driver.py
│   └── ultrasonic.py
├── ipc/
│   └── queues.py
├── processes/
│   ├── audio_process.py
│   ├── camera_process.py
│   ├── decision_process.py
│   ├── motor_process.py
│   ├── ultrasonic_process.py
│   └── vision_process.py
├── tests/
│   ├── test_camera.py
│   ├── test_motor.py
│   └── test_ultrasonic.py
└── utils/
    ├── logger.py
    └── timing.py
```

---

## GPIO and Runtime Configuration
All pin numbers and thresholds are centralized in:
- `config/settings.py`

Update this file before running on real hardware:
- motor pins (`IN1`, `IN2`, `IN3`, `IN4`, `ENA`, `ENB`)
- ultrasonic pins (`TRIG`, `ECHO`)
- camera index and frame size
- obstacle threshold distance
- process timing intervals

---

## How to Run
From project root:
```bash
python main.py
```

If your Pi setup needs elevated GPIO/camera permissions:
```bash
sudo python main.py
```

Shutdown:
- Press `Ctrl + C` in terminal.
- `main.py` sets shared stop event and performs clean process shutdown.

---

## Module Test Scripts (Recommended First)
Test modules individually before full integration:

Motor test:
```bash
python tests/test_motor.py
```

Ultrasonic test:
```bash
python tests/test_ultrasonic.py
```

Camera test:
```bash
python tests/test_camera.py
```

---

## Safety Notes
- Keep wheels lifted during first motor tests.
- Do not power motors directly from Raspberry Pi 5V.
- Use a shared common ground between Pi and L298N.
- Protect Pi from 5V `ECHO` using a voltage divider/level shifter.
- Always stop power before rewiring.

---

## Development Notes
- The hardware modules include fail-safe behavior and exception handling to reduce crash risk.
- Process queues are bounded to prevent latency and memory growth.
- On non-Pi systems, GPIO-dependent modules can run in dry-run mode for development.

---

## Authors
- Mukesh Mani Tripathi
- Leon Dhoska