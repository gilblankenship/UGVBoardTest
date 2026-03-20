# UGV01 Raspberry Pi 5 Control Server

Controls the Waveshare UGV01 board from a Raspberry Pi 5 over serial.
The ESP32 firmware stays on the board — this Python app sends JSON commands
and serves a web control interface from the Pi.

## Hardware Connection

Connect the ESP32 board to the Pi via USB cable, or wire the GPIO UART:

| Pi 5 GPIO | ESP32     | Function |
|-----------|-----------|----------|
| GPIO 14   | RX (GPIO 3) | UART TX  |
| GPIO 15   | TX (GPIO 1) | UART RX  |
| GND       | GND       | Ground   |

USB is simpler — just plug in the USB cable. The board appears as `/dev/ttyUSB0`.

## Setup

```bash
cd rpi
bash setup.sh
```

## Run

```bash
source venv/bin/activate

# USB connection (default)
python main.py

# GPIO UART
python main.py --port /dev/ttyAMA0

# Custom web port
python main.py --web-port 80

# Serial REPL only (no web server)
python main.py --no-web
```

Open `http://<pi-ip>:8080` in a browser for the web control interface.

## REST API

In addition to the original ESP32-compatible web endpoints (`/cmd`, `/js`, `/deviceInfo`),
the Pi server adds REST endpoints:

```
POST /api/stop                          # emergency stop
POST /api/speed    {"left":0.5,"right":0.5}  # set motor speed
GET  /api/imu                           # IMU data
GET  /api/power                         # voltage/current/power
GET  /api/encoders                      # wheel speeds
POST /api/servo/pwm  {"pos":90}         # PWM servo
POST /api/servo/bus  {"id":1,"pos":2047}  # bus servo
POST /api/cmd        {"T":70}           # raw JSON command
```

## Python API

```python
from ugv.board import UGVBoard

board = UGVBoard("/dev/ttyUSB0")
board.connect()

board.set_speed(0.5, 0.5)    # forward
board.emergency_stop()

info = board.get_imu_info()
print(info)

board.disconnect()
```
