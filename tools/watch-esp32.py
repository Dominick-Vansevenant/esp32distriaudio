import argparse
import re
import sys
import time

import serial


def main():
    parser = argparse.ArgumentParser(description="Read ESP32 serial logs.")
    parser.add_argument("--port", default="COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.3)
    end = time.time() + args.seconds
    buf = b""
    try:
        while time.time() < end:
            data = ser.read(4096)
            if data:
                buf += data
    finally:
        ser.close()

    text = buf.decode("utf-8", "replace")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    sys.stdout.buffer.write(text.encode("ascii", "replace"))


if __name__ == "__main__":
    main()
