# Vision-Based Autonomous Robot with OS-Level Multi-Process Scheduling

## 📌 Overview
This project implements an autonomous mobile robot using Raspberry Pi, designed to demonstrate core Operating System (OS) concepts such as process management, CPU scheduling, inter-process communication (IPC), and real-time execution.

The robot uses a combination of computer vision and ultrasonic sensing to navigate its environment safely and efficiently.

---

## 🚀 Features
- Real-time video processing using OpenCV
- Ultrasonic sensor-based obstacle detection (safety override)
- Multi-process architecture using Python multiprocessing
- Priority-based task scheduling
- Inter-process communication (IPC) using queues
- Autonomous navigation (forward, turn, stop)
- Optional audio alerts

---

## 🧠 OS Concepts Demonstrated
- Process Management (parallel execution)
- CPU Scheduling (priority-based)
- Inter-Process Communication (queues/shared memory)
- Synchronization (safe process coordination)
- Memory Management (image frame handling)
- Real-Time Constraints (low latency response)

---

## 🧰 Hardware Requirements
- Raspberry Pi (with Raspberry Pi OS)
- Camera Module
- Ultrasonic Sensor (HC-SR04)
- L298N Motor Driver
- 4WD Robot Chassis with Motors
- Battery Pack
- Speaker (optional)
- Jumper Wires

---

## 💻 Software Requirements
- Python 3.x
- OpenCV
- RPi.GPIO / gpiozero
- multiprocessing (built-in)

Install dependencies:
```bash
pip install opencv-python gpiozero
```

## Project Structure
```bash
robot-os-project/
│
├── README.md
├── requirements.txt
├── main.py                  # Entry point
│
├── config/
│   └── settings.py          # Pin configs, thresholds
│
├── processes/
│   ├── camera_process.py    # Capture frames
│   ├── vision_process.py    # Image processing
│   ├── ultrasonic_process.py # Distance sensing
│   ├── decision_process.py  # Decision logic
│   ├── motor_process.py     # Motor control
│   └── audio_process.py     # Alerts 
│
├── ipc/
│   └── queues.py            # Shared queues setup
│
├── hardware/
│   ├── motor_driver.py      # L298N control
│   ├── ultrasonic.py        # Sensor logic
│   └── camera.py            # Camera interface
│
├── utils/
│   ├── logger.py            # Logging
│   └── timing.py            # Performance metrics
│
├── tests/
│   ├── test_motor.py
│   ├── test_ultrasonic.py
│   └── test_camera.py
│
└── docs/
    ├── architecture.png
    └── report.pdf
```

## ⚙️ How to Run

Clone the repository:
```bash
git clone <your-repo-link>
cd robot-os-project
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the system:
```bash
python main.py
```

## 🔄 System Workflow

- Camera captures frames
- Vision process detects obstacles
- Ultrasonic sensor checks distance
- Decision process determines action
- Motor process executes movement

## 📊 Performance Metrics

- Response Time (ms)
- CPU Usage (%)
- Frame Processing Time
- Obstacle Detection Accuracy

## ⚠️ Notes

- Ensure correct GPIO pin configuration
- Run with sudo if required:
```bash
sudo python main.py
```
- Test each module individually before full integration

## 📌 Future Improvements

- Add deep learning-based object detection
- Web dashboard for monitoring
- Advanced scheduling algorithms
- ROS integration

## 👨‍💻 Authors

Mukesh Mani Tripathi
Leon Dhoska