# UGV01_BASE Board Test

ESP32-based firmware for the Waveshare UGV01 unmanned ground vehicle. Built with PlatformIO and Arduino framework.

## Features

- Dual DC motor control with encoder feedback and PI speed control
- 9-DOF IMU (QMI8658 + AK09918) for orientation sensing
- WiFi AP/STA with web-based control interface
- PWM servo and bus servo (FEETECH STS) support
- INA219 power monitoring
- SSD1306 OLED status display
- JSON command interface over serial and HTTP

## Hardware

| Component | Interface | Pins |
|-----------|-----------|------|
| Motor A | PWM + DIR | PWM: 25, DIR: 17/21 |
| Motor B | PWM + DIR | PWM: 26, DIR: 22/23 |
| Encoder A | Interrupt | 34/35 |
| Encoder B | Interrupt | 16/27 |
| IMU (QMI8658/AK09918) | I2C | SDA: 32, SCL: 33 |
| INA219 | I2C (0x42) | SDA: 32, SCL: 33 |
| SSD1306 OLED | I2C (0x3C) | SDA: 32, SCL: 33 |
| PWM Servo | PWM | GPIO 4 |
| Bus Servo | UART1 | RX: 18, TX: 19 |
| IR Cut | GPIO | GPIO 5 |

## Getting Started

### Build and Upload

```bash
pio run -t upload
```

### Serial Monitor

```bash
pio device monitor
```

Baud rate: 115200

### WiFi Connection

By default the board tries to connect to a known WiFi network for 20 seconds. If it fails, it starts an access point:

- **SSID**: `UGV01_BASE`
- **Password**: `12345678`
- **Web UI**: `http://192.168.4.1`

Edit `include/config.h` to change WiFi credentials or default mode.

## Serial JSON Commands

| Command | JSON |
|---------|------|
| Emergency Stop | `{"T":0}` |
| Speed Input | `{"T":1,"L":0.5,"R":0.5}` |
| PID Set | `{"T":2,"P":170,"I":90}` |
| OLED Text | `{"T":3,"lineNum":0,"Text":"hello"}` |
| PWM Servo | `{"T":40,"pos":90,"spd":30}` |
| Bus Servo | `{"T":50,"id":1,"pos":2047,"spd":500,"acc":30}` |
| WiFi Info | `{"T":65}` |
| IMU Info | `{"T":71}` |
| Device Info | `{"T":74}` |

## Dependencies

- [ArduinoJson](https://github.com/bblanchon/ArduinoJson) v6
- [INA219_WE](https://github.com/wollewald/INA219_WE)
- [Adafruit SSD1306](https://github.com/adafruit/Adafruit_SSD1306)
- [ESP32Servo](https://github.com/madhephaestus/ESP32Servo)
- [SCServo](https://registry.platformio.org/libraries/workloads/SCServo)
