#!/usr/bin/env python3
import json
import os
import re
import socket
import subprocess
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


SNAPCAST_HOST = os.environ.get("SNAPCAST_HOST", "127.0.0.1")
SNAPCAST_PORT = int(os.environ.get("SNAPCAST_PORT", "1705"))
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8080"))
METRICS_INTERVAL = int(os.environ.get("METRICS_INTERVAL", "5"))
LOG_DIR = Path(os.environ.get("LOG_DIR", "/data/logs"))
STATIC_DIR = Path(__file__).with_name("static")
CLIENT_LABELS = {}

for item in os.environ.get("SNAPCAST_CLIENT_LABELS", "").split(","):
    if "=" in item:
        key, value = item.split("=", 1)
        CLIENT_LABELS[key.strip().lower()] = value.strip()

metrics_lock = threading.Lock()
metrics = deque(maxlen=1440)
rpc_counter = 10


def rpc(method, params=None, timeout=3):
    global rpc_counter
    rpc_counter += 1
    request = {"id": rpc_counter, "jsonrpc": "2.0", "method": method}
    if params is not None:
        request["params"] = params

    with socket.create_connection((SNAPCAST_HOST, SNAPCAST_PORT), timeout=timeout) as sock:
        sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
        sock.settimeout(timeout)
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk

    response = json.loads(data.decode("utf-8"))
    if "error" in response:
        raise RuntimeError(response["error"])
    return response.get("result")


def get_snap_status():
    return rpc("Server.GetStatus")


def flatten_clients(status):
    server = status.get("server", {})
    groups = server.get("groups", [])
    clients = []
    for group in groups:
        for client in group.get("clients", []):
            host = client.get("host", {})
            cfg = client.get("config", {})
            client_id = client.get("id", "")
            mac = host.get("mac", client_id)
            name = cfg.get("name") or CLIENT_LABELS.get(client_id.lower()) or CLIENT_LABELS.get(mac.lower())
            if not name:
                name = host.get("name") or client_id[-8:] or "unknown"
            clients.append(
                {
                    "id": client_id,
                    "mac": mac,
                    "name": name,
                    "ip": host.get("ip", ""),
                    "connected": bool(client.get("connected")),
                    "group_id": group.get("id", ""),
                    "group_name": group.get("name", ""),
                    "stream_id": group.get("stream_id", ""),
                    "latency": cfg.get("latency", 0),
                    "volume": cfg.get("volume", {}),
                    "last_seen": client.get("lastSeen", {}),
                }
            )
    return clients


def ping_host(ip):
    if not ip:
        return {"ok": False, "rtt_ms": None, "error": "no ip"}
    try:
        proc = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "rtt_ms": None, "error": str(exc)}

    match = re.search(r"time[=<]([0-9.]+)\s*ms", proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "rtt_ms": float(match.group(1)) if match else None,
        "error": "" if proc.returncode == 0 else proc.stderr.strip() or proc.stdout.strip()[-160:],
    }


def process_up(pattern):
    proc = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, check=False)
    return proc.returncode == 0


def collect_metrics_once():
    item = {
        "ts": int(time.time()),
        "services": {
            "snapserver": process_up("snapserver"),
            "librespot": process_up("librespot"),
            "ffmpeg": process_up("ffmpeg"),
            "avahi": process_up("avahi-daemon"),
        },
        "clients": [],
        "snapcast_ok": False,
        "error": "",
    }
    try:
        status = get_snap_status()
        item["snapcast_ok"] = True
        for client in flatten_clients(status):
            ping = ping_host(client["ip"])
            item["clients"].append(
                {
                    "id": client["id"],
                    "name": client["name"],
                    "ip": client["ip"],
                    "connected": client["connected"],
                    "group_id": client["group_id"],
                    "stream_id": client["stream_id"],
                    "rtt_ms": ping["rtt_ms"],
                    "ping_ok": ping["ok"],
                }
            )
    except Exception as exc:
        item["error"] = str(exc)

    with metrics_lock:
        metrics.append(item)


def metrics_loop():
    while True:
        collect_metrics_once()
        time.sleep(max(2, METRICS_INTERVAL))


def tail_file(path, max_bytes=60000):
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes), os.SEEK_SET)
            data = handle.read().decode("utf-8", "replace")
            if size > max_bytes:
                data = "... truncated ...\n" + data
            return data
    except FileNotFoundError:
        return ""


def journal_tail(unit, lines=300):
    try:
        proc = subprocess.run(
            ["journalctl", "-u", unit, "-n", str(lines), "--no-pager"],
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_json(self, payload, code=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_static(self, path):
        if path == "/":
            path = "/index.html"
        file_path = (STATIC_DIR / path.lstrip("/")).resolve()
        if STATIC_DIR.resolve() not in file_path.parents and file_path != STATIC_DIR.resolve():
            self.send_error(404)
            return
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content_type = "text/html; charset=utf-8"
        if file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif file_path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            try:
                status = get_snap_status()
                with metrics_lock:
                    history = list(metrics)
                self.send_json(
                    {
                        "ok": True,
                        "snapcast": status,
                        "clients": flatten_clients(status),
                        "metrics": history[-240:],
                        "services": history[-1]["services"] if history else {},
                    }
                )
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 503)
            return

        if parsed.path == "/api/logs":
            query = parse_qs(parsed.query)
            name = query.get("name", ["snapserver"])[0]
            allowed = {
                "snapserver": (LOG_DIR / "snapserver.log", "snapserver.service"),
                "librespot": (LOG_DIR / "librespot.log", "librespot-snapcast.service"),
                "dashboard": LOG_DIR / "dashboard.log",
                "idle-mute": LOG_DIR / "idle-mute.log",
            }
            if name not in allowed:
                self.send_json({"ok": False, "error": "unknown log"}, 400)
                return
            target = allowed[name]
            if isinstance(target, tuple):
                text = tail_file(target[0]) or journal_tail(target[1])
            else:
                text = tail_file(target)
            self.send_json({"ok": True, "name": name, "text": text})
            return

        self.send_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/snapcast":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            action = payload.get("action")
            if action == "set_group_clients":
                result = rpc("Group.SetClients", {"id": payload["group_id"], "clients": payload["clients"]})
            elif action == "set_group_stream":
                result = rpc("Group.SetStream", {"id": payload["group_id"], "stream_id": payload["stream_id"]})
            elif action == "set_group_name":
                result = rpc("Group.SetName", {"id": payload["group_id"], "name": payload["name"]})
            elif action == "set_client_volume":
                result = rpc(
                    "Client.SetVolume",
                    {
                        "id": payload["client_id"],
                        "volume": {
                            "percent": int(payload.get("percent", 100)),
                            "muted": bool(payload.get("muted", False)),
                        },
                    },
                )
            elif action == "set_client_latency":
                result = rpc("Client.SetLatency", {"id": payload["client_id"], "latency": int(payload["latency"])})
            else:
                self.send_json({"ok": False, "error": "unknown action"}, 400)
                return
            collect_metrics_once()
            self.send_json({"ok": True, "result": result})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=metrics_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", DASHBOARD_PORT), Handler)
    print(f"dashboard listening on 0.0.0.0:{DASHBOARD_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
