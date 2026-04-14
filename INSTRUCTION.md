# Raspberry Pi Setup and Run Instructions

## Step 1 - Flash Raspberry Pi OS (Only Once)

If your Pi is not set up yet, use **Raspberry Pi Imager**.

1. Insert SD card into your laptop.
2. Open Raspberry Pi Imager.
3. Select:
   - **OS** -> Raspberry Pi OS (64-bit)
   - **Storage** -> your SD card
4. Click **Write**.

## Step 2 - Boot Raspberry Pi

1. Insert the SD card into the Pi.
2. Power it on.
3. Complete initial setup (Wi-Fi, username, etc.).

## Step 3 - Get Your Code onto Raspberry Pi

You have three practical options:

### Option 1 (Best): Use GitHub (Recommended)

Run on Raspberry Pi terminal:

```bash
sudo apt update
sudo apt install git -y
git clone <your-repo-link>
cd robot-os-project
```

### Option 2: Copy Using USB

1. Put your project folder on a USB drive.
2. Plug the USB into the Pi.
3. Copy it:

```bash
cp -r /media/pi/USB/robot-os-project ~/
```

### Option 3: Use SCP (From Your Laptop)

Run on your laptop:

```bash
scp -r robot-os-project pi@<raspberry-pi-ip>:/home/pi/
```

## Step 4 - Install Dependencies

Inside your project folder:

```bash
cd robot-os-project
pip3 install -r requirements.txt
```

### Important: OpenCV Issue Fix

If OpenCV installation fails:

```bash
sudo apt install python3-opencv
```

## Step 5 - Enable Hardware (Camera + GPIO)

Run:

```bash
sudo raspi-config
```

Enable:
- **Interface** -> **Camera** -> **Enable**

Then reboot:

```bash
sudo reboot
```

## Step 6 - Run Your Project

```bash
cd robot-os-project
python3 main.py
```

If you get GPIO permission issues:

```bash
sudo python3 main.py
```

## Step 7 - Test Modules Individually (Very Important)

Before running the full system, test each module:

```bash
python3 tests/test_motor.py
python3 tests/test_ultrasonic.py
python3 tests/test_camera.py
```