# Vision-Based Autonomous Robot with OS-Level Multi-Process Scheduling

## Overview

This project builds a **Raspberry Pi autonomous robot** that demonstrates Operating System concepts through a real multi-process control pipeline. The robot autonomously navigates using computer vision and ultrasonic sensing while showcasing fundamental OS principles in a practical, hardware-integrated system.

### Key Features

The robot combines:
- **Camera-based vision processing** – Scene analysis with OpenCV and optional YOLO object detection
- **Ultrasonic obstacle avoidance** – Real-time distance sensing with safety-first override
- **Motor control** – Precise L298N PWM-driven movement
- **Optional audio signaling** – Beep alerts on obstacle detection

### Core Operating System Concepts Demonstrated

- **Concurrent Process Execution** – 6 independent worker processes running simultaneously
- **Inter-Process Communication (IPC)** – Queue-based message passing between processes
- **Clear Task Separation** – Each process handles a specific responsibility (camera, vision, decision, motor control, etc.)
- **Priority-Based Behavior** – Safety (ultrasonic) overrides navigation (vision)
- **Resource Management** – Bounded queues, timeout handling, graceful shutdown
- **Real-Time Constraints** – Polling intervals tuned for responsive robot behavior

---

## Implemented Architecture

### Process Overview

The system spawns **6 independent worker processes** that communicate via thread-safe queues:

| Process | Purpose | Input | Output |
|---------|---------|-------|--------|
| **UltrasonicProcess** | Obstacle detection & safety monitoring | GPIO TRIG/ECHO pins | `distance_queue`, `audio_queue` (on danger) |
| **CameraProcess** | Frame acquisition from camera hardware | Camera device | `frame_queue`, `preview_queue` |
| **VisionProcess** | Scene analysis (contours, objects) | `frame_queue` | `vision_result_queue` (objects/obstacles) |
| **DecisionProcess** | Motion planning (combines vision + safety) | `vision_result_queue`, `distance_queue` | `decision_queue` (movement commands) |
| **MotorProcess** | Motor command execution via PWM | `decision_queue` | GPIO motor pins |
| **AudioProcess** | Buzzer/speaker alerts | `audio_queue` | GPIO audio pin |

### Data Flow Diagram

```
┌──────────────┐
│   Camera     │
└──────┬───────┘
       │ (raw frames)
       ▼
┌──────────────────┐
│ CameraProcess    │
└──────┬───────────┘
       │ frame_queue
       ├─────────────────────────────┐
       │                             │
       ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│ VisionProcess    │        │ Dashboard        │
│ (detect objects) │        │ (live preview)   │
└──────┬───────────┘        └──────────────────┘
       │ vision_result_queue
       │
       ▼
┌──────────────────────────────┐
│ DecisionProcess              │◄──────────────────┐
│ (plan movement)              │                   │
└──────┬───────────────────────┘         distance_queue
       │ decision_queue          ┌──────────────────┐
       │                         │UltrasonicProcess │
       │                         │(detect obstacles)│
       │                         └────┬─────────────┘
       │                             │ (on danger)
       │                             ▼
       ▼                      ┌──────────────────┐
┌──────────────────┐         │AudioProcess      │
│MotorProcess      │         │(beep alert)      │
│(execute movement)│         └──────────────────┘
└──────────────────┘
```

### Process Lifecycle

1. **Main Process** (`main.py`)
   - Creates IPC queues and shared `stop_event`
   - Spawns all child processes with a small delay between each
   - Starts the GUI dashboard for real-time monitoring
   - Handles graceful shutdown on Ctrl+C

2. **Child Processes** (run in parallel)
   - Each process runs an infinite loop checking its input queues
   - Uses non-blocking queue gets with timeouts to prevent deadlock
   - Responds to the shared `stop_event` to shutdown cleanly

3. **Shutdown Sequence**
   - GUI closes → `stop_event.set()` is called
   - All child processes detect `stop_event` and exit their loops
   - Main process joins each child process (2-second timeout)
   - Unresponsive processes are terminated forcefully

---

## Hardware Requirements

### Core Components

| Component | Model | Purpose | Qty |
|-----------|-------|---------|-----|
| **Raspberry Pi** | Pi 4 or Pi 5 (2GB+ RAM) | Main processor | 1 |
| **Camera** | Pi Camera V2 or USB Webcam | Vision input | 1 |
| **Motor Driver** | L298N Dual H-Bridge | Motor control | 1 |
| **Ultrasonic Sensor** | HC-SR04 | Obstacle detection | 1 |
| **DC Motors** | 3-6V with gearbox | Wheel drive | 2-4 |
| **4WD Chassis** | Plastic or aluminum | Robot body | 1 |
| **Buzzer** | 5V Active Buzzer | Audio alerts | 1 |
| **Power** | 5V for Pi, 6-12V for motors | Power supply | 2 |

### Wiring Overview (GPIO Pin Mapping)

All GPIO assignments are defined in `config/settings.py`. Default mappings:

#### Motor Control (L298N)
```
Raspberry Pi GPIO  →  L298N Pin
Pin 17 (GPIO17)    →  IN1
Pin 27 (GPIO27)    →  IN2
Pin 22 (GPIO22)    →  IN3
Pin 23 (GPIO23)    →  IN4
Pin 18 (GPIO18)    →  ENA (PWM)
Pin 24 (GPIO24)    →  ENB (PWM)
```

#### Ultrasonic Sensor (HC-SR04)
```
Raspberry Pi GPIO  →  HC-SR04 Pin
Pin 5 (GPIO5)      →  TRIG
Pin 6 (GPIO6)      →  ECHO (with voltage divider!)
5V                 →  VCC
GND                →  GND
```

**⚠️ CRITICAL**: The HC-SR04 ECHO pin outputs 5V but Raspberry Pi GPIO is 3.3V tolerant.
Use a voltage divider (e.g., 10kΩ + 20kΩ resistors) to protect the Pi.

#### Audio (Buzzer)
```
Raspberry Pi GPIO  →  Buzzer
Pin 25 (GPIO25)    →  Signal
5V or 3.3V         →  VCC (check buzzer specs)
GND                →  GND
```

#### Camera
- **Pi Camera Module**: Connected via CSI ribbon cable (on designated camera port)
- **USB Camera**: Plugged into any USB port

### Power Considerations

- **Raspberry Pi**: Requires stable 5V, ~2.5A supply
- **DC Motors**: Use separate power supply (6-12V, ~2-3A depending on load)
- **Common Ground**: Pi, L298N, and motor power supply **must share a common ground**
- **Never** power motors directly from Pi's 5V output—it will cause brownout and crashes

### Assembly Checklist

- [ ] Raspberry Pi OS flashed to SD card (64-bit recommended)
- [ ] Chassis assembled with motors and wheels installed
- [ ] L298N motor driver soldered/connected to motor outputs
- [ ] HC-SR04 connected with voltage divider on ECHO pin
- [ ] Camera connected and enabled in raspi-config
- [ ] Buzzer wired to GPIO25
- [ ] All power supplies connected with common ground
- [ ] Code cloned or transferred to Pi
- [ ] Dependencies installed via `pip3 install -r requirements.txt`

---

## Software Requirements

### Core Dependencies

The project requires **Python 3.10+** and the following packages:

| Package | Purpose |
|---------|---------|
| **numpy** | Numerical array operations |
| **opencv-python** | Computer vision (image processing, contour detection) |
| **Pillow** | Image manipulation |
| **imutils** | OpenCV utilities (contour filtering, etc.) |
| **gpiozero** | GPIO abstraction (fallback/cross-platform support) |
| **RPi.GPIO** | Low-level Raspberry Pi GPIO (required on Pi) |
| **picamera2** | *Pi-only* – Modern camera interface for Pi Camera Module |
| **ultralytics** | *Optional* – YOLO object detection (enable in settings) |
| **PyQt5** or **tkinter** | GUI dashboard (usually pre-installed) |

### Installation

#### On Raspberry Pi (Recommended)

1. **Update system packages:**
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt install -y python3-pip python3-dev git python3-tk
   ```

3. **Clone the project:**
   ```bash
   git clone <repository-url>
   cd vision-os-robot_26
   ```

4. **Create virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python packages:**
   ```bash
   pip3 install -r requirements.txt
   ```

6. **Install optional Pi-specific packages:**
   ```bash
   sudo apt install -y python3-gpiozero python3-rpi.gpio python3-opencv python3-picamera2
   ```

#### On Development Machine (Windows/Mac/Linux)

For testing code without hardware:

```bash
pip install -r requirements.txt
python main.py  # Runs in dry-run mode (no GPIO/camera hardware)
```

**Note**: Most hardware-dependent imports will fail gracefully on non-Pi systems. The dashboard may not display camera feed, but process communication works.

---

## Project Structure

```bash
vision-os-robot_26/
├── main.py                          # Entry point - spawns all processes
├── requirements.txt                 # Python package dependencies
├── README.md                        # This file
├── INSTRUCTION.md                   # Step-by-step Raspberry Pi setup guide
├── LICENSE                          # Project license
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # ⚠️ EDIT THIS - GPIO pins & thresholds
│
├── hardware/                         # Hardware abstraction layer
│   ├── __init__.py
│   ├── camera.py                    # Camera capture (OpenCV or picamera2)
│   ├── motor_driver.py              # L298N PWM motor control
│   ├── audio.py                     # Buzzer/speaker control
│   └── ultrasonic.py                # HC-SR04 distance sensor
│
├── ipc/                              # Inter-Process Communication
│   ├── __init__.py
│   └── queues.py                    # Creates all queue objects
│
├── processes/                        # Worker processes (main OS concepts)
│   ├── __init__.py
│   ├── camera_process.py            # Captures camera frames continuously
│   ├── vision_process.py            # Analyzes frames (contours, YOLO)
│   ├── ultrasonic_process.py        # Measures distance, sets danger flags
│   ├── decision_process.py          # Combines vision + safety → movement
│   ├── motor_process.py             # Executes motor commands (fwd, back, turn)
│   └── audio_process.py             # Plays beep alerts
│
├── ui/                               # User interface
│   ├── __init__.py
│   └── dashboard.py                 # PyQt5/Tkinter real-time monitoring UI
│
├── tests/                            # Unit and integration tests
│   ├── __init__.py
│   ├── test_camera.py               # Camera module test
│   ├── test_motor.py                # Motor control test
│   ├── test_ultrasonic.py           # Distance sensor test
│   ├── test_audio.py                # Audio output test
│   └── test_motor_channels.py       # Motor channel mapping test
│
├── utils/                            # Utility modules
│   ├── __init__.py
│   ├── logger.py                    # Logging configuration
│   ├── status.py                    # Status message structures
│   └── timing.py                    # Performance timing utilities
│
└── image/                            # (Optional) Stored images/logs

---

## Configuration

### GPIO and Runtime Settings

**All configuration is centralized in** [config/settings.py](config/settings.py) **— edit this file before running on hardware:**

#### Motor Driver (L298N)
```python
MOTOR_IN1, MOTOR_IN2          # Left motor direction pins (GPIO 17, 27)
MOTOR_IN3, MOTOR_IN4          # Right motor direction pins (GPIO 22, 23)
MOTOR_ENA, MOTOR_ENB          # Left/Right PWM pins (GPIO 18, 24)
MOTOR_DEFAULT_SPEED = 70      # 0-100, PWM duty cycle
MOTOR_LEFT_TRIM = 0           # Adjust if left motor is slower/faster
MOTOR_RIGHT_TRIM = 0          # Adjust if right motor is slower/faster
LEFT_MOTOR_INVERT = False     # Set True if motor spins backwards
RIGHT_MOTOR_INVERT = False    # Set True if motor spins backwards
```

#### Ultrasonic Sensor (HC-SR04)
```python
ULTRASONIC_TRIG_PIN = 5       # Trigger pin (GPIO 5)
ULTRASONIC_ECHO_PIN = 6       # Echo pin (GPIO 6, needs voltage divider!)
OBSTACLE_THRESHOLD_CM = 20.0  # Distance to trigger "obstacle detected"
OBSTACLE_HYSTERESIS_CM = 2.0  # Hysteresis to avoid jitter
ULTRASONIC_POLL_INTERVAL_SEC = 0.08  # Polling frequency
```

#### Camera Settings
```python
CAMERA_INDEX = 0              # 0 for /dev/video0 (USB) or Pi Camera
FRAME_WIDTH = 640             # Capture resolution
FRAME_HEIGHT = 480
PREVIEW_WIDTH = 640           # Dashboard display resolution
PREVIEW_HEIGHT = 480
FRAME_QUEUE_SIZE = 2          # Bounded queue (prevent latency)
CAMERA_POLL_INTERVAL_SEC = 0.03
```

#### Process Polling Intervals (Tunable for Performance)
```python
VISION_POLL_INTERVAL_SEC = 0.03       # Vision processing rate
DECISION_POLL_INTERVAL_SEC = 0.02     # Decision-making rate
MOTOR_POLL_INTERVAL_SEC = 0.02        # Motor command check rate
AUDIO_POLL_INTERVAL_SEC = 0.1         # Audio alert rate
QUEUE_GET_TIMEOUT_SEC = 0.1           # Queue timeout (prevents blocking)
```

#### Audio (Buzzer)
```python
AUDIO_PIN = 25                # GPIO 25
BEEP_FREQUENCY_HZ = 1100      # Tone frequency
BEEP_DURATION_SEC = 0.25      # Beep length
BEEP_COOLDOWN_SEC = 0.7       # Minimum time between beeps
```

#### Vision Processing
```python
VISION_MIN_CONTOUR_AREA = 1100        # Min object size (pixels²)
VISION_BOX_CENTER_DEADZONE = 0.15     # Center tolerance (15% of frame)
VISION_STOP_AREA_RATIO = 0.22         # Object fills 22% → stop
YOLO_ENABLED = False                  # Enable ML object detection
YOLO_MODEL_PATH = "models/yolov8n.pt" # YOLO model file
YOLO_CONFIDENCE = 0.45                # Detection confidence threshold
```

### How to Customize

1. Edit [config/settings.py](config/settings.py)
2. Match GPIO pins to your wiring (use `raspi-config` to verify camera/SPI/I2C if needed)
3. Run tests first to verify individual hardware:
   ```bash
   python tests/test_motor.py
   python tests/test_ultrasonic.py
   python tests/test_camera.py
   ```
4. Adjust thresholds based on your environment (lighting, distance, motor speed)

---

## Quick Start

### On Raspberry Pi

1. **Ensure hardware is connected** (motors lifted, camera attached, etc.)
2. **Edit configuration:**
   ```bash
   nano config/settings.py
   # Verify GPIO pins match your wiring
   ```
3. **Run the robot:**
   ```bash
   cd /path/to/vision-os-robot_26
   python3 main.py
   ```
   Or with elevated permissions:
   ```bash
   sudo python3 main.py
   ```

4. **Monitor robot:**
   - A dashboard window opens showing:
     - Live camera feed with detected objects
     - Current distance to obstacles
     - Motor speeds and directions
     - Process health status
   - **Stop:** Press `Ctrl + C` in terminal or close the dashboard

### On Development Machine (Dry-Run Mode)

To test the code without hardware:

```bash
python main.py
```

The system will:
- Skip GPIO operations (gracefully)
- Simulate camera with generated frames
- Run all processes and queues normally
- Show the dashboard (if GUI libs available)

This is useful for testing the multiprocessing logic before Pi deployment.

---

## How to Run - Detailed

### Full System Startup

```bash
python main.py
```

**Startup sequence:**
1. Logging is configured
2. IPC queues and shared `stop_event` created
3. 6 child processes spawn (with 50ms stagger between each)
4. Dashboard starts and begins monitoring processes
5. Processes enter their main loops:
   - UltrasonicProcess: Polls distance sensor every 80ms
   - CameraProcess: Captures frames every 30ms
   - VisionProcess: Analyzes frames every 30ms
   - DecisionProcess: Plans movement every 20ms
   - MotorProcess: Executes commands every 20ms
   - AudioProcess: Handles alerts every 100ms

### Shutdown Sequence

**Graceful shutdown (Ctrl+C or close dashboard):**
1. `stop_event.set()` is called
2. All child processes detect event and exit their loops
3. Each process joins with a 2-second timeout
4. Unresponsive processes are forcefully terminated
5. All GPIO pins are cleaned up
6. Program exits

### Headless Mode (No GUI)

If the dashboard fails to start (no X server, missing PyQt5, etc.), the system falls back to **headless mode**:
- Processes still run normally
- No real-time visualization
- Monitor via logs only
- Press `Ctrl + C` to shutdown

---

## Dashboard Features

The real-time monitoring dashboard provides:

| Feature | Shows |
|---------|-------|
| **Camera Feed** | Live video with detected objects highlighted |
| **Distance Gauge** | Current ultrasonic distance reading |
| **Status Panel** | Active processes (green = running, red = stopped) |
| **Command Log** | Recent motor commands (forward, back, turn) |
| **FPS Counter** | Frame processing rate |

**Controls:**
- Close window to trigger shutdown
- Resize window as needed

---

## Testing Individual Modules

**It's strongly recommended to test hardware modules individually before running the full system.**

### Motor Control Test

Tests left and right motor movement:

```bash
python tests/test_motor.py
```

**What it does:**
- Spins left motor forward/backward
- Spins right motor forward/backward
- Tests PWM speed control
- Measures motor response

**Expected output:**
- Motors should spin smoothly without stuttering
- No smoke or burning smell
- Forward should move wheels forward, backward should reverse

**Troubleshooting:**
- If motor doesn't spin: Check GPIO pins in `settings.py`, verify motor power supply
- If motor spins weakly: Increase `MOTOR_DEFAULT_SPEED` in settings
- If motor spins backwards: Set `LEFT_MOTOR_INVERT` or `RIGHT_MOTOR_INVERT` to `True`

### Ultrasonic Sensor Test

Tests distance measurement:

```bash
python tests/test_ultrasonic.py
```

**What it does:**
- Continuously reads distance measurements
- Prints distance every 500ms
- Detects obstacles within threshold

**Expected output:**
```
Distance: 45.2 cm
Distance: 44.8 cm
Obstacle detected!
Distance: 12.5 cm
```

**Troubleshooting:**
- If no output: Check GPIO pins, verify sensor power/ground
- If readings are 0 or unrealistic: Check voltage divider on ECHO pin
- If readings jump wildly: Add small delays, check sensor alignment

### Camera Test

Tests camera capture and frame processing:

```bash
python tests/test_camera.py
```

**What it does:**
- Captures frames from camera
- Detects contours (objects in frame)
- Displays live feed with detected objects highlighted
- Shows FPS counter

**Expected output:**
- Window shows live camera feed
- Objects highlighted with green boxes
- FPS ~20-30 on Pi

**Troubleshooting:**
- If no window appears: Check `CAMERA_INDEX` in settings
- If "camera not found": Enable Camera in `raspi-config`, reboot
- If frames are black: Check camera cable connection, lighting

### Motor Channels Test

Tests correct motor pin mapping:

```bash
python tests/test_motor_channels.py
```

**Expected output:**
```
Testing motor channels...
Spin 1: [forward] -> wheels should move forward
Spin 2: [backward] -> wheels should move backward
Spin 3: [left turn] -> robot should turn left
Spin 4: [right turn] -> robot should turn right
```

---

## Running Individual Process Tests

To test the multiprocessing architecture without full hardware, you can run individual process tests. See [tests/](tests/) directory for available tests.

---

## Safety Notes

⚠️ **Before powering hardware, review these critical points:**

### Electrical Safety

- **Separate power supplies**: Do NOT power motors from Raspberry Pi's 5V output
  - Motors draw 2-3A; Pi can only supply ~500mA
  - This causes voltage drop → Pi crashes or reboots randomly
  - Use a dedicated 6-12V battery/PSU for motors

- **Common ground connection**: Pi, L298N, and motor power supply **must share a common ground** (GND)
  - Connect all GND pins together
  - Without this, signals are floating and unreliable

- **HC-SR04 Echo protection**: The ECHO pin outputs 5V but Pi GPIO is 3.3V max
  - Use a voltage divider: 10kΩ (to ECHO) + 20kΩ (to GND)
  - Without it, you risk permanently damaging the GPIO pin

- **Always disconnect power before rewiring**
  - Hot-swapping can damage electronics and cause short circuits

### Mechanical Safety

- **Keep wheels lifted during first motor tests**
  - Don't let the robot drive off a table until you've tested movement
  - Test on a bench with suspended wheels first

- **Secure the robot**
  - Mount on a test stand or block the wheels during initial testing
  - Place a stop barrier if testing on the floor

- **Check motor connections**
  - Verify motor wires are firmly soldered/connected
  - Loose connections can cause intermittent shorts

### Software Safety

- **Emergency stop (Ctrl+C)**
  - Always have hands on Ctrl+C to stop the robot immediately
  - The system uses `stop_event` for graceful shutdown

- **Test obstacle avoidance**
  - Run in a clear, enclosed space first
  - Test ultrasonic thresholds in your environment
  - Different lighting and surfaces affect sensor readings

---

## Troubleshooting

### Robot Won't Start

| Issue | Cause | Solution |
|-------|-------|----------|
| ImportError: No module named 'RPi.GPIO' | Dependencies not installed | Run `pip3 install -r requirements.txt` |
| Permission denied on GPIO | Missing sudo | Run `sudo python3 main.py` |
| "Camera not found" error | Camera not enabled | Run `sudo raspi-config`, enable camera, reboot |

### Motors Not Spinning

| Issue | Cause | Solution |
|-------|-------|----------|
| Motors unresponsive | Wrong GPIO pins | Check `config/settings.py` matches your wiring |
| Motor spins backwards | Motor wired backwards | Set `LEFT_MOTOR_INVERT = True` or `RIGHT_MOTOR_INVERT = True` |
| Motors stutter or jitter | Insufficient power | Use external power supply, check common ground |
| One motor is slower | Speed imbalance | Adjust `MOTOR_LEFT_TRIM` or `MOTOR_RIGHT_TRIM` |

### Ultrasonic Not Working

| Issue | Cause | Solution |
|-------|-------|----------|
| No distance readings | Sensor not powered or wired | Check TRIG/ECHO pins, verify 5V connection |
| Readings all 0 or very large | ECHO pin damaged | Use voltage divider, don't directly connect 5V ECHO to 3.3V pin |
| Readings unstable | Sensor misaligned or dirty | Point sensor at obstacle, clean lens |

### Camera Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Black or blank frames | Camera not enabled | Run `sudo raspi-config`, enable camera |
| "Cannot open device /dev/video0" | Wrong camera index | Change `CAMERA_INDEX` in settings.py |
| Camera freezes or slow FPS | Pi overloaded | Reduce `FRAME_WIDTH` and `FRAME_HEIGHT`, close other programs |
| Camera won't initialize | Camera ribbon cable loose | Reseat camera ribbon in CSI port |

### Process Crashes or Segfaults

| Issue | Cause | Solution |
|-------|-------|----------|
| Process exits immediately | Exception during initialization | Check process logs, verify GPIO is available |
| Random crashes during runtime | Pi overheating | Add heatsinks, improve ventilation, reduce polling rates |
| Processes hang (frozen) | Deadlock in queue communication | Check process timeouts in `settings.py`, ensure all queues are properly created |

### Dashboard Won't Display

| Issue | Cause | Solution |
|-------|-------|----------|
| "No module named 'tkinter'" | GUI library missing | Install: `sudo apt install python3-tk` |
| Window doesn't appear (X server) | Headless system or SSH without X11 | System falls back to headless mode (no GUI, logs only) |
| GUI is slow/laggy | Too many processes or high resolution | Reduce `PREVIEW_WIDTH`/`PREVIEW_HEIGHT` in settings |

---

## Performance Tuning

### Optimize for Speed (Real-Time Navigation)

```python
# In config/settings.py
FRAME_WIDTH = 320             # Smaller = faster processing
FRAME_HEIGHT = 240
VISION_MIN_CONTOUR_AREA = 800 # Fewer false detections
VISION_POLL_INTERVAL_SEC = 0.02  # Faster vision loop
DECISION_POLL_INTERVAL_SEC = 0.01 # Faster decisions
```

### Optimize for Accuracy (Careful Navigation)

```python
FRAME_WIDTH = 800             # Larger = more detail
FRAME_HEIGHT = 600
VISION_MIN_CONTOUR_AREA = 1500   # Stricter filtering
OBSTACLE_THRESHOLD_CM = 25.0     # More conservative
YOLO_ENABLED = True              # Use ML for better detection
```

### Pi Zero / Low-Power Boards

```python
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
CAMERA_POLL_INTERVAL_SEC = 0.05   # Slower capture
VISION_POLL_INTERVAL_SEC = 0.05   # Slower processing
# Disable YOLO, use contour detection only
YOLO_ENABLED = False
```

---

## Development & Architecture

### Key Design Principles

1. **Isolation via Multiprocessing**
   - Each hardware component runs in its own process
   - Crash in one process doesn't crash others
   - Processes share data only through queues (thread-safe)

2. **Queue-Based IPC**
   - All inter-process communication uses Python queues
   - Bounded queue sizes (e.g., `FRAME_QUEUE_SIZE = 2`) prevent memory bloat
   - Non-blocking `get()` with timeouts prevents deadlock

3. **Graceful Degradation**
   - Missing hardware (camera, GPIO) doesn't crash the system
   - Modules return empty/default data on error
   - Dashboard works in headless mode

4. **Configurable Everything**
   - All constants in `config/settings.py`
   - No hardcoded values in process or hardware code
   - Easy to adapt to different hardware setups

### How Processes Communicate

**Example: Obstacle Detection → Beep Alert**

```
UltrasonicProcess detects obstacle:
  1. Reads GPIO (TRIG/ECHO pins)
  2. Computes distance
  3. If distance < OBSTACLE_THRESHOLD_CM:
     → ipc.audio_queue.put({"beep": True})

AudioProcess waiting on audio_queue:
  1. Receives beep command
  2. Triggers GPIO audio pin
  3. Sleeps for BEEP_DURATION_SEC
```

### Adding New Functionality

#### Add a New Sensor (Example: Light Sensor)

1. Create hardware module: `hardware/light_sensor.py`
   ```python
   def read_light_level():
       # Read sensor value via ADC/GPIO
       return light_value
   ```

2. Create process: `processes/light_process.py`
   ```python
   def light_process(light_queue, stop_event):
       while not stop_event.is_set():
           level = read_light_level()
           light_queue.put({"light": level})
           time.sleep(0.1)
   ```

3. Add queue in `ipc/queues.py`:
   ```python
   class IPCObjects:
       light_queue = mp.Queue(maxsize=5)
   ```

4. Spawn process in `main.py`:
   ```python
   mp.Process(name="LightProcess", target=light_process, args=(ipc.light_queue, ipc.stop_event))
   ```

5. Consume in `decision_process.py`:
   ```python
   light_data = ipc.light_queue.get(timeout=0.1)
   if light_data["light"] < DARK_THRESHOLD:
       # Turn on LED or adjust speed
   ```

### Testing Without Hardware

- All modules gracefully handle missing GPIO/camera
- `test_*.py` files demonstrate isolated testing patterns
- Process logic can be unit-tested independently
- Use dry-run mode to test multiprocessing pipeline

### Logging and Debugging

The system uses Python's standard `logging` module:

```python
from utils.logger import get_logger
logger = get_logger(__name__)
logger.info("Camera initialized")
logger.error("Motor failed: %s", error)
```

**Enable debug logs:** Set `ENABLE_DEBUG_LOGS = True` in `settings.py`

All logs are printed to console and (optionally) written to file.

### Common Patterns in Code

**Non-blocking queue read with timeout:**
```python
try:
    data = queue.get(timeout=QUEUE_GET_TIMEOUT_SEC)
except queue.Empty:
    data = None  # No data available
```

**Graceful shutdown:**
```python
while not stop_event.is_set():
    # Do work
    time.sleep(interval)
```

**Status reporting:**
```python
status_queue.put({
    "process": "MotorProcess",
    "status": "moving_forward",
    "speed": 70,
    "timestamp": time.time()
})
```

---

## Development Notes

- **Hardware modules** include fail-safe behavior and exception handling to reduce crash risk
- **Process queues** are bounded to prevent latency and memory growth
- **Non-Pi systems** have GPIO-dependent modules run in dry-run mode (return default values)
- **Logging** is configured per module with both console and file output
- **All tests** can run on Windows/Mac/Linux without hardware

---

## FAQ

**Q: Can I run this on Raspberry Pi Zero?**  
A: Yes, but with reduced performance. Reduce frame size and disable YOLO object detection.

**Q: Do I need the exact same hardware?**  
A: No. The code is modular. You can swap sensors/motors as long as you update `settings.py` and the hardware abstraction layers.

**Q: How do I add a second camera?**  
A: Create `processes/camera_process_2.py` that reads from a different `CAMERA_INDEX`. Merge feeds in `vision_process.py`.

**Q: Can I run this on a robot arm instead of a wheeled robot?**  
A: Yes! Replace motor_process.py with servo control logic. The same IPC/multiprocessing architecture applies.

**Q: What's the latency from sensor to motor?**  
A: Typically 50-100ms depending on polling intervals. Ultrasonic (80ms) is the slowest; vision+decision is ~60ms.

**Q: Can I add machine learning (YOLO)?**  
A: Yes! Set `YOLO_ENABLED = True` in settings.py and install `pip install ultralytics`. The model download is automatic.

**Q: How do I record robot movement/sensor data?**  
A: Add a logging process that consumes from all queues and writes to CSV/JSON. See utils/logger.py for patterns.

**Q: Can I control the robot remotely (WiFi/Bluetooth)?**  
A: Yes. Add a process that reads from a socket/serial port and injects commands into `decision_queue`. Completely modular!

---

## Useful Links & References

### Raspberry Pi Official Resources
- [Raspberry Pi GPIO Documentation](https://www.raspberrypi.com/documentation/computers/gpio/)
- [Raspberry Pi OS Setup Guide](https://www.raspberrypi.com/documentation/computers/getting-started.html)
- [Camera Module Setup](https://www.raspberrypi.com/documentation/accessories/camera.html)

### Hardware Component Datasheets
- [L298N Motor Driver Datasheet](https://www.st.com/en/motor-drivers/l298.html)
- [HC-SR04 Ultrasonic Sensor Guide](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

### Python & Computer Vision
- [OpenCV Python Tutorials](https://docs.opencv.org/master/d9/df8/tutorial_root.html)
- [Python Multiprocessing Documentation](https://docs.python.org/3/library/multiprocessing.html)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)

### Educational OS Concepts
- [Linux Process Management](https://www.linux.org/threads/what-is-a-process.8971/)
- [Inter-Process Communication (IPC)](https://en.wikipedia.org/wiki/Inter-process_communication)
- [Real-Time Systems Overview](https://en.wikipedia.org/wiki/Real-time_computing)

---

## Contributors & Support

### Authors
- **Mukesh Mani Tripathi** — Project lead, multiprocessing architecture
- **Leon Dhoska** — Hardware integration, testing

### Getting Help

If you encounter issues:
1. **Check the Troubleshooting section** above
2. **Run individual tests** (test_motor.py, test_camera.py, etc.)
3. **Enable debug logs** in config/settings.py
4. **Review process logs** in utils/logger.py
5. **Post an issue** on the project repository (if available)

---

## License

This project is provided under the terms in [LICENSE](LICENSE).

---

## Acknowledgments

- Inspired by real-world robotics and OS education at Towson University
- Built on proven Python multiprocessing patterns
- Thanks to the OpenCV and Raspberry Pi communities

---

**Last Updated:** May 2026  
**Python Version:** 3.10+  
**Tested On:** Raspberry Pi 4/5 with Raspberry Pi OS (64-bit)