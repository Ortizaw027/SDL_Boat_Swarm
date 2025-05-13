# Unmanned Surface Vehicle Swarm

## Project Overview

This project implements a coordinated swarm of Unmanned Surface Vehicles (USVs) using a Leader-Follower architecture and LoRa wireless communication, supported by a centralized controller and a custom Python control stack.

**Authors:** Dominic Mesagna & Antonio Ortiz
**Institution:** SUNY Polytechnic Institute – Department of Electrical and Computer Engineering
**Sponsor:** Drone City

## Key Features

* Autonomous route-following with heading and GPS feedback.
* Real-time swarm coordination using RSSI-based formation maintenance.
* Centralized GUI-based controller for monitoring and command issuance.
* Full modular Python codebase, easily extendable to more followers.

## Repository Structure

* `LeaderBoat.py`: Main control script for the leader boat.
* `FollowerBoat.py`: Main control script for each follower boat.
* `Controller.py`: Script running on the Controller Pi, handling LoRa-USB relay.
* `GUI.py`: Python/Tkinter-based GUI for starting/stopping the swarm and monitoring data.
* `sensor_test_programs/`: Standalone scripts for motor, GPS, compass, and LoRa testing.

## How to Use the Code

### 1. Transfer Code Files to the Raspberry Pis

**Method 1: WinSCP (Recommended for Windows users)**

* Download WinSCP: [https://winscp.net](https://winscp.net)
* Connect via SFTP to your Pi (username/password as configured during setup).
* Drag and drop `.py` scripts into the `/home/pi` directory.

**Method 2: nano (Manual copy-paste)**

* SSH into your Pi:

  ```bash
  ssh pi@<your_pi_ip>
  ```
* Create and edit the script:

  ```bash
  nano LeaderBoat.py
  ```
* Paste the code and save (`Ctrl+X`, then `Y`, then `Enter`).

### 2. Run the Programs Manually

On each Pi:

```bash
python3 LeaderBoat.py
python3 FollowerBoat.py
python3 Controller.py
```

On the laptop:

```bash
python3 GUI.py
```

Press `Ctrl+C` to stop any script manually.

---

### 3. \[Optional] Auto-Run Scripts on Boot

Use `systemd` to create services:

```bash
sudo nano /etc/systemd/system/leaderboat.service
```

Paste:

```ini
[Unit]
Description=Leader Boat Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/LeaderBoat.py
WorkingDirectory=/home/pi
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable leaderboat.service
sudo systemctl start leaderboat.service
```

Repeat with `followerboat.service` or `controller.service` as needed.

---

## Additional Notes

* Each boat has a unique hardcoded LoRa address (e.g., 101 = Leader, 102 = Follower).
* The Controller Pi communicates with the GUI over USB serial (`/dev/ttyGS0`) and with boats via LoRa.
* Test scripts are included to validate each sensor/module independently before full integration.

## Troubleshooting Tips

* **Boot Loop**: Unplug, reseat SD card, and reconnect power.
* **No GPS Data**: Ensure pigpiod is running; check TX (GPIO27) wiring.
* **Compass Jitter**: Mount compass flat and away from motors.
* **No LoRa Communication**: Check serial port wiring and LoRa IDs.
* **GUI Not Receiving Data**: Confirm USB Gadget mode is active and `/dev/ttyGS0` exists.

## Demo Video

🎥 [Watch Project Demo](https://youtube.com/shorts/xEofub0lBZo?feature=share)
