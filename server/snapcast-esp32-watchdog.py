#!/usr/bin/env python3
import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_STATE_PATH = Path("/var/lib/esp32distriaudio/esp32-watchdog-state.json")


def rpc(method, params=None, host="127.0.0.1", port=1705, timeout=3):
    payload = {"id": 1, "jsonrpc": "2.0", "method": method}
    if params is not None:
        payload["params"] = params
    message = json.dumps(payload) + "\n"
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(message.encode("utf-8"))
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    response = json.loads(b"".join(chunks).decode("utf-8").strip())
    if "error" in response:
        raise RuntimeError(response["error"])
    return response.get("result")


def iter_clients(status):
    for group in status["server"].get("groups", []):
        for client in group.get("clients", []):
            yield client


def is_esp32_client(client):
    host = client.get("host", {})
    snapclient = client.get("snapclient", {})
    return (
        client.get("connected") is True
        and host.get("arch") == "xtensa"
        and host.get("os") == "esp32"
        and snapclient.get("name") == "libsnapcast"
    )


def ping_ok(ip, probes=3, timeout=1):
    for _ in range(probes):
        proc = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0:
            return True
    return False


def tcp_sessions_for_ip(ip):
    proc = subprocess.run(
        ["ss", "-tnp"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    sessions = []
    pattern = re.compile(rf"192\.168\.\d+\.\d+:1704\s+{re.escape(ip)}:(\d+)")
    for line in proc.stdout.splitlines():
        match = pattern.search(line)
        if match:
            sessions.append(match.group(1))
    return sessions


def kill_tcp_sessions(ip):
    sessions = tcp_sessions_for_ip(ip)
    if not sessions:
        return False, sessions

    proc = subprocess.run(
        ["ss", "--kill", "--tcp", "state", "established", "dst", ip, "sport", "=", ":1704"],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (proc.stdout + proc.stderr).strip()
    if output:
        print(output)
    return True, sessions


def load_state(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(description="Recover half-dead ESP32 Snapcast client sessions.")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--probes", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    status = rpc("Server.GetStatus")
    state = load_state(args.state)
    seen = set()

    for client in iter_clients(status):
        if not is_esp32_client(client):
            continue

        client_id = client["id"]
        ip = client.get("host", {}).get("ip", "")
        seen.add(client_id)
        if not ip:
            continue

        if ping_ok(ip, probes=args.probes, timeout=args.timeout):
            if state.get(client_id, {}).get("failures"):
                print(f"{client_id} {ip}: reachable again, reset failure count")
            state[client_id] = {"ip": ip, "failures": 0, "last_seen": int(time.time())}
            continue

        entry = state.get(client_id, {"ip": ip, "failures": 0})
        entry["ip"] = ip
        entry["failures"] = int(entry.get("failures", 0)) + 1
        entry["last_failure"] = int(time.time())
        state[client_id] = entry
        print(f"{client_id} {ip}: unreachable failure {entry['failures']}/{args.threshold}")

        if entry["failures"] >= args.threshold:
            if args.dry_run:
                print(f"{client_id} {ip}: would close stale Snapcast TCP session")
            else:
                killed, sessions = kill_tcp_sessions(ip)
                if killed:
                    print(f"{client_id} {ip}: closed stale Snapcast TCP sessions {sessions}")
                else:
                    print(f"{client_id} {ip}: no Snapcast TCP session found to close")
            entry["failures"] = 0
            entry["last_action"] = int(time.time())

    for client_id in list(state):
        if client_id not in seen:
            state.pop(client_id, None)

    save_state(args.state, state)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"watchdog error: {exc}", file=sys.stderr)
        raise
