#!/usr/bin/env python3
import argparse
import re
import statistics
import subprocess
import time


def ping_once(ip, timeout):
    proc = subprocess.run(
        ["ping", "-c", "1", "-W", str(timeout), ip],
        text=True,
        capture_output=True,
        check=False,
    )
    match = re.search(r"time[=<]([0-9.]+) ms", proc.stdout)
    if proc.returncode == 0 and match:
        return float(match.group(1))
    return None


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * pct / 100) - 1))
    return ordered[index]


def main():
    parser = argparse.ArgumentParser(description="Measure ESP32 ping jitter.")
    parser.add_argument("ips", nargs="+")
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--timeout", type=int, default=1)
    parser.add_argument("--interval", type=float, default=0.05)
    args = parser.parse_args()

    for ip in args.ips:
        values = []
        lost = 0
        for _ in range(args.count):
            value = ping_once(ip, args.timeout)
            if value is None:
                lost += 1
            else:
                values.append(value)
            time.sleep(args.interval)

        if not values:
            print(f"{ip}: all lost ({lost}/{args.count})")
            continue

        print(
            f"{ip}: ok={len(values)} lost={lost} "
            f"avg={statistics.mean(values):.1f}ms "
            f"p95={percentile(values, 95):.1f}ms max={max(values):.1f}ms"
        )


if __name__ == "__main__":
    main()
