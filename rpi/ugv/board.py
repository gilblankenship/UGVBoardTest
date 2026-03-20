"""Serial interface to the UGV01 ESP32 board.

Sends JSON commands over serial and parses JSON responses.
All command types match the ESP32 firmware's T-code protocol.
"""

import json
import threading
import time
from typing import Optional

import serial


class UGVBoard:
    """Communicate with the UGV01 board over serial."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._lock = threading.Lock()

    def connect(self):
        """Open the serial connection."""
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
        )
        # Give ESP32 time to reset after serial open
        time.sleep(2)
        # Drain any startup messages
        self._serial.reset_input_buffer()

    def disconnect(self):
        """Close the serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._serial = None

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def send_command(self, cmd: dict) -> Optional[dict]:
        """Send a JSON command and read back the JSON response (if any).

        Returns parsed JSON dict, or None if no JSON response received.
        """
        with self._lock:
            if not self.is_connected:
                raise ConnectionError("Not connected to board")

            payload = json.dumps(cmd, separators=(",", ":")) + "\n"
            self._serial.write(payload.encode("ascii"))
            self._serial.flush()

            # Read response lines, looking for JSON
            response = self._read_json_response()
            return response

    def _read_json_response(self, max_lines: int = 10, line_timeout: float = 0.5) -> Optional[dict]:
        """Read lines until we find a JSON object or exhaust attempts."""
        old_timeout = self._serial.timeout
        self._serial.timeout = line_timeout
        try:
            for _ in range(max_lines):
                line = self._serial.readline().decode("ascii", errors="replace").strip()
                if not line:
                    break
                if line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
        finally:
            self._serial.timeout = old_timeout
        return None

    # ── Motor Control ─────────────────────────────────────────

    def emergency_stop(self) -> Optional[dict]:
        """Stop all motors immediately."""
        return self.send_command({"T": 0})

    def set_speed(self, left: float, right: float) -> Optional[dict]:
        """Set motor speeds. Values roughly -1.0 to 1.0 (m/s)."""
        return self.send_command({"T": 1, "L": left, "R": right})

    def set_pid(self, kp: float, ki: float, kd: float = 0) -> Optional[dict]:
        """Tune PID parameters."""
        return self.send_command({"T": 2, "P": kp, "I": ki, "D": kd})

    # ── OLED Display ──────────────────────────────────────────

    def oled_set(self, line_num: int, text: str) -> Optional[dict]:
        """Set OLED display line (0-3)."""
        return self.send_command({"T": 3, "lineNum": line_num, "Text": text})

    def oled_default(self) -> Optional[dict]:
        """Reset OLED to default display mode."""
        return self.send_command({"T": -3})

    # ── PWM Servo ─────────────────────────────────────────────

    def pwm_servo(self, pos: int, spd: int = 30) -> Optional[dict]:
        """Move PWM servo to position (0-180 degrees)."""
        return self.send_command({"T": 40, "pos": pos, "spd": spd})

    def pwm_servo_mid(self) -> Optional[dict]:
        """Move PWM servo to center (90 degrees)."""
        return self.send_command({"T": -4})

    # ── Bus Servo ─────────────────────────────────────────────

    def bus_servo(self, servo_id: int, pos: int, spd: int = 500, acc: int = 30) -> Optional[dict]:
        """Move bus servo to position."""
        return self.send_command({"T": 50, "id": servo_id, "pos": pos, "spd": spd, "acc": acc})

    def bus_servo_mid(self, servo_id: int) -> Optional[dict]:
        """Move bus servo to center position."""
        return self.send_command({"T": -5, "id": servo_id})

    def bus_servo_scan(self, max_id: int = 20) -> Optional[dict]:
        """Scan for connected bus servos."""
        return self.send_command({"T": 52, "num": max_id})

    def bus_servo_info(self, servo_id: int) -> Optional[dict]:
        """Get bus servo info (position, speed, temp, voltage)."""
        return self.send_command({"T": 53, "id": servo_id})

    def bus_servo_set_id(self, old_id: int, new_id: int) -> Optional[dict]:
        """Change bus servo ID."""
        return self.send_command({"T": 54, "old": old_id, "new": new_id})

    def bus_servo_torque_lock(self, servo_id: int, status: int) -> Optional[dict]:
        """Enable/disable bus servo torque (1=on, 0=off)."""
        return self.send_command({"T": 55, "id": servo_id, "status": status})

    def bus_servo_torque_limit(self, servo_id: int, limit: int) -> Optional[dict]:
        """Set bus servo torque limit (0-1000)."""
        return self.send_command({"T": 56, "id": servo_id, "limit": limit})

    def bus_servo_mode(self, servo_id: int, mode: int) -> Optional[dict]:
        """Set bus servo mode (0=servo, 3=wheel)."""
        return self.send_command({"T": 57, "id": servo_id, "mode": mode})

    # ── Sensors ───────────────────────────────────────────────

    def get_power_info(self) -> Optional[dict]:
        """Get INA219 power data (voltage, current, power)."""
        return self.send_command({"T": 70})

    def get_imu_info(self) -> Optional[dict]:
        """Get IMU data (angles, accel, gyro, magnetometer, temp)."""
        return self.send_command({"T": 71})

    def get_encoder_info(self) -> Optional[dict]:
        """Get encoder speeds (left/right m/s)."""
        return self.send_command({"T": 73})

    def get_device_info(self) -> Optional[dict]:
        """Get device info (Kp value)."""
        return self.send_command({"T": 74})

    # ── IR Cut ────────────────────────────────────────────────

    def ir_cut(self, status: int) -> Optional[dict]:
        """Control IR cut filter (0=off, 1=on)."""
        return self.send_command({"T": 80, "status": status})

    # ── Speed Rate ────────────────────────────────────────────

    def set_speed_rate(self, left: float, right: float) -> Optional[dict]:
        """Set speed rate multipliers."""
        return self.send_command({"T": 901, "L": left, "R": right})

    def get_speed_rate(self) -> Optional[dict]:
        """Get current speed rate multipliers."""
        return self.send_command({"T": 902})

    def save_speed_rate(self) -> Optional[dict]:
        """Save speed rates to NVS."""
        return self.send_command({"T": 903})

    # ── NVS ───────────────────────────────────────────────────

    def get_nvs_space(self) -> Optional[dict]:
        """Get free NVS space."""
        return self.send_command({"T": 904})

    def nvs_clear(self) -> Optional[dict]:
        """Clear all NVS data."""
        return self.send_command({"T": 905})
