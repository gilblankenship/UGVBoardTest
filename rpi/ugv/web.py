"""Flask web server for UGV01 control.

Provides the same HTTP API as the ESP32's built-in web server,
plus serves the control interface.
"""

import json
import os
import threading
import time

from flask import Flask, jsonify, render_template, request

from .board import UGVBoard

# Shared board instance and latest sensor cache
_board: UGVBoard = None
_device_cache = {}
_device_cache_lock = threading.Lock()
_speed_level = 2  # 0=slow, 1=middle, 2=fast
_last_feedback = ""


def create_app(board: UGVBoard) -> Flask:
    global _board
    _board = board

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    )

    # ── Pages ─────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("index.html")

    # ── Device info (polled by the web UI) ────────────────

    @app.route("/deviceInfo")
    def device_info():
        """Return cached sensor data as JSON."""
        with _device_cache_lock:
            return jsonify(_device_cache)

    # ── Motor command (from directional buttons) ──────────

    @app.route("/cmd")
    def cmd():
        global _speed_level
        cmd_type = int(request.args.get("inputA", 0))
        val_b = float(request.args.get("inputB", 0))
        val_c = float(request.args.get("inputC", 0))

        if cmd_type == 1:
            multiplier = [0.3, 0.6, 1.0][_speed_level]
            _board.set_speed(val_b * multiplier, val_c * multiplier)
        elif cmd_type == 2:
            _speed_level = int(val_b)

        return "", 200

    # ── JSON passthrough ──────────────────────────────────

    @app.route("/js")
    def js_passthrough():
        global _last_feedback
        raw = request.args.get("json", "{}")
        try:
            cmd_dict = json.loads(raw)
        except json.JSONDecodeError:
            return "invalid json", 400
        result = _board.send_command(cmd_dict)
        _last_feedback = json.dumps(result) if result else ""
        return "", 200

    @app.route("/jsfb")
    def js_feedback():
        return _last_feedback, 200, {"Content-Type": "text/plain"}

    # ── REST-style API (new, RPi-native) ──────────────────

    @app.route("/api/stop", methods=["POST"])
    def api_stop():
        _board.emergency_stop()
        return jsonify({"ok": True})

    @app.route("/api/speed", methods=["POST"])
    def api_speed():
        data = request.get_json(force=True)
        result = _board.set_speed(data.get("left", 0), data.get("right", 0))
        return jsonify(result or {"ok": True})

    @app.route("/api/imu")
    def api_imu():
        return jsonify(_board.get_imu_info() or {})

    @app.route("/api/power")
    def api_power():
        return jsonify(_board.get_power_info() or {})

    @app.route("/api/encoders")
    def api_encoders():
        return jsonify(_board.get_encoder_info() or {})

    @app.route("/api/servo/pwm", methods=["POST"])
    def api_pwm_servo():
        data = request.get_json(force=True)
        result = _board.pwm_servo(data.get("pos", 90))
        return jsonify(result or {"ok": True})

    @app.route("/api/servo/bus", methods=["POST"])
    def api_bus_servo():
        data = request.get_json(force=True)
        result = _board.bus_servo(
            data["id"], data["pos"],
            data.get("spd", 500), data.get("acc", 30),
        )
        return jsonify(result or {"ok": True})

    @app.route("/api/cmd", methods=["POST"])
    def api_raw_cmd():
        """Send any raw JSON command to the board."""
        data = request.get_json(force=True)
        result = _board.send_command(data)
        return jsonify(result or {"ok": True})

    return app


def _sensor_poll_loop(board: UGVBoard, interval: float = 0.5):
    """Background thread that polls sensor data for the web UI."""
    global _device_cache
    while True:
        try:
            power = board.get_power_info() or {}
            imu = board.get_imu_info() or {}
            data = {
                "V": round(power.get("load_V", -1), 2),
                "r": round(imu.get("roll", 0), 2),
                "p": round(imu.get("pitch", 0), 2),
                "y": round(imu.get("yaw", 0), 2),
                "mX": imu.get("magn_X", 0),
                "mY": imu.get("magn_Y", 0),
                "mZ": imu.get("magn_Z", 0),
                "IP": "RPi",
                "MAC": "",
                "RSSI": 0,
                "SPEED": _speed_level,
            }
            with _device_cache_lock:
                _device_cache = data
        except Exception:
            pass
        time.sleep(interval)


def start_sensor_polling(board: UGVBoard, interval: float = 0.5):
    """Start the background sensor polling thread."""
    t = threading.Thread(target=_sensor_poll_loop, args=(board, interval), daemon=True)
    t.start()
