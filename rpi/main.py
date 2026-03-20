#!/usr/bin/env python3
"""UGV01 Raspberry Pi Control Server.

Connects to the UGV01 ESP32 board over serial and serves a web control
interface on the Pi's network.

Usage:
    python main.py                          # defaults: /dev/ttyUSB0, port 8080
    python main.py --port /dev/ttyAMA0      # use GPIO UART
    python main.py --web-port 80            # serve on port 80 (needs root)
    python main.py --no-web                 # serial only, no web server
"""

import argparse
import signal
import sys
import time

from ugv.board import UGVBoard
from ugv.web import create_app, start_sensor_polling


def main():
    parser = argparse.ArgumentParser(description="UGV01 RPi Control Server")
    parser.add_argument(
        "--port", default="/dev/ttyUSB0",
        help="Serial port for the ESP32 board (default: /dev/ttyUSB0)",
    )
    parser.add_argument(
        "--baud", type=int, default=115200,
        help="Serial baud rate (default: 115200)",
    )
    parser.add_argument(
        "--web-port", type=int, default=8080,
        help="Web server port (default: 8080)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Web server bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--no-web", action="store_true",
        help="Don't start the web server (serial REPL only)",
    )
    args = parser.parse_args()

    # Connect to the board
    board = UGVBoard(port=args.port, baudrate=args.baud)
    print(f"Connecting to {args.port} at {args.baud} baud...")

    try:
        board.connect()
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    print("Connected to UGV01 board.")

    # Graceful shutdown
    def shutdown(sig, frame):
        print("\nShutting down...")
        board.emergency_stop()
        board.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if args.no_web:
        # Interactive serial REPL
        print("Serial REPL mode. Type JSON commands, or 'quit' to exit.")
        print('Example: {"T":1,"L":0.5,"R":0.5}')
        while True:
            try:
                cmd = input(">>> ")
            except EOFError:
                break
            if cmd.strip().lower() in ("quit", "exit", "q"):
                break
            if not cmd.strip():
                continue
            import json
            try:
                parsed = json.loads(cmd)
                result = board.send_command(parsed)
                if result:
                    print(json.dumps(result, indent=2))
                else:
                    print("(no JSON response)")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
        board.emergency_stop()
        board.disconnect()
    else:
        # Start web server with sensor polling
        start_sensor_polling(board, interval=0.5)
        app = create_app(board)
        print(f"Web UI at http://{args.host}:{args.web_port}")
        app.run(host=args.host, port=args.web_port, threaded=True)


if __name__ == "__main__":
    main()
