#!/usr/bin/env python3
import json
import os
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


SNAPCAST_HOST = os.environ.get("SNAPCAST_HOST", "127.0.0.1")
SNAPCAST_PORT = int(os.environ.get("SNAPCAST_PORT", "1705"))
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", "8080"))
METRICS_INTERVAL = int(os.environ.get("METRICS_INTERVAL", "5"))
LOG_DIR = Path(os.environ.get("LOG_DIR", "/data/logs"))
DEFAULT_STATE_DIR = "/data" if Path("/data").exists() else "/var/lib/esp32distriaudio"
STATE_FILE = Path(os.environ.get("DASHBOARD_STATE_FILE", str(Path(DEFAULT_STATE_DIR) / "dashboard-state.json")))
STATIC_DIR = Path(__file__).with_name("static")
CLIENT_LABELS = {}

for item in os.environ.get("SNAPCAST_CLIENT_LABELS", "").split(","):
    if "=" in item:
        key, value = item.split("=", 1)
        CLIENT_LABELS[key.strip().lower()] = value.strip()

metrics_lock = threading.Lock()
state_lock = threading.Lock()
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


def read_dashboard_state():
    with state_lock:
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data.setdefault("virtual_groups", [])
        return data


def write_dashboard_state(data):
    with state_lock:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def dashboard_groups(status):
    groups = []
    changed = False
    data = read_dashboard_state()
    for group in data.get("virtual_groups", []):
        if not group.get("id") or not str(group.get("id")).startswith("dash-"):
            changed = True
            continue
        if "clients" not in group:
            group["clients"] = []
            changed = True
        groups.append(group)
    if changed:
        data["virtual_groups"] = groups
        write_dashboard_state(data)
    return groups


def flatten_clients(status):
    server = status.get("server", {})
    groups = server.get("groups", [])
    clients = []
    for group in groups:
        for client in group.get("clients", []):
            host = client.get("host", {})
            cfg = client.get("config", {})
            client_id = client.get("id", "")
            if not client.get("connected") and host.get("arch") != "xtensa":
                continue
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


def client_quality(history, client_id, window=60):
    samples = []
    for item in history[-window:]:
        for client in item.get("clients", []):
            if client.get("id") == client_id:
                samples.append(client)
                break
    if not samples:
        return {
            "state": "unknown",
            "label": "geen meting",
            "loss_percent": None,
            "avg_ms": None,
            "max_ms": None,
            "samples": 0,
        }

    ok = [sample for sample in samples if sample.get("ping_ok")]
    rtts = [sample.get("rtt_ms") for sample in ok if sample.get("rtt_ms") is not None]
    max_rtts = [sample.get("rtt_max_ms", sample.get("rtt_ms")) for sample in ok if sample.get("rtt_max_ms", sample.get("rtt_ms")) is not None]
    if any("loss_percent" in sample for sample in samples):
        loss_percent = round(sum(float(sample.get("loss_percent", 100.0)) for sample in samples) / len(samples), 1)
    else:
        loss_percent = round(100 * (len(samples) - len(ok)) / len(samples), 1)
    avg_ms = round(sum(rtts) / len(rtts), 1) if rtts else None
    max_ms = round(max(max_rtts), 1) if max_rtts else None

    if loss_percent > 5 or (max_ms is not None and max_ms > 1000):
        state = "bad"
        label = "onbetrouwbaar"
    elif loss_percent > 0 or (max_ms is not None and max_ms > 250) or (avg_ms is not None and avg_ms > 50):
        state = "warn"
        label = "jitter"
    else:
        state = "good"
        label = "stabiel"

    return {
        "state": state,
        "label": label,
        "loss_percent": loss_percent,
        "avg_ms": avg_ms,
        "max_ms": max_ms,
        "samples": len(samples),
    }


def enrich_clients(clients, history):
    return [{**client, "quality": client_quality(history, client.get("id", ""))} for client in clients]


def find_group(status, group_id):
    for group in status.get("server", {}).get("groups", []):
        if group.get("id") == group_id:
            return group
    return None


def find_client_group(status, client_id):
    for group in status.get("server", {}).get("groups", []):
        if any(client.get("id") == client_id for client in group.get("clients", [])):
            return group
    return None


def create_virtual_group(name):
    clean_name = (name or "").strip() or "Nieuwe groep"
    data = read_dashboard_state()
    group = {"id": f"dash-{int(time.time() * 1000)}", "name": clean_name, "clients": []}
    data["virtual_groups"].append(group)
    write_dashboard_state(data)
    return group


def delete_virtual_group(group_id):
    data = read_dashboard_state()
    before = len(data.get("virtual_groups", []))
    data["virtual_groups"] = [group for group in data.get("virtual_groups", []) if group.get("id") != group_id]
    write_dashboard_state(data)
    return {"deleted": before != len(data["virtual_groups"])}


def virtual_group_by_id(group_id):
    for group in read_dashboard_state().get("virtual_groups", []):
        if group.get("id") == group_id:
            return group
    return None


def update_virtual_group(group_id, mutator):
    data = read_dashboard_state()
    for group in data.get("virtual_groups", []):
        if group.get("id") == group_id:
            group.setdefault("clients", [])
            result = mutator(group)
            write_dashboard_state(data)
            return result if result is not None else group
    raise RuntimeError("dashboard group not found")


def set_virtual_group_name(group_id, name):
    clean_name = (name or "").strip() or "Nieuwe groep"
    return update_virtual_group(group_id, lambda group: group.update({"name": clean_name}) or group)


def add_virtual_group_client(group_id, client_id):
    def mutate(group):
        if client_id not in group["clients"]:
            group["clients"].append(client_id)
        return group

    return update_virtual_group(group_id, mutate)


def remove_virtual_group_client(group_id, client_id):
    def mutate(group):
        group["clients"] = [item for item in group["clients"] if item != client_id]
        return group

    return update_virtual_group(group_id, mutate)


def activate_virtual_group(group_id):
    group = virtual_group_by_id(group_id)
    if not group:
        raise RuntimeError("dashboard group not found")
    clients = [client_id for client_id in group.get("clients", []) if client_id]
    if not clients:
        raise RuntimeError("groep bevat nog geen devices")

    status = get_snap_status()
    target_group = None
    for client_id in clients:
        target_group = find_client_group(status, client_id)
        if target_group:
            break
    if not target_group:
        raise RuntimeError("geen actieve Snapcast client gevonden voor deze groep")

    result = rpc("Group.SetClients", {"id": target_group.get("id"), "clients": clients})
    rpc("Group.SetName", {"id": target_group.get("id"), "name": group.get("name", "Nieuwe groep")})
    return result


def move_client_to_group(client_id, target_group_id):
    status = get_snap_status()
    target = find_group(status, target_group_id)
    source = find_client_group(status, client_id)
    if not source:
        raise RuntimeError("client not found")

    if target:
        clients = [client.get("id") for client in target.get("clients", []) if client.get("id")]
        if client_id not in clients:
            clients.append(client_id)
        return rpc("Group.SetClients", {"id": target_group_id, "clients": clients})

    virtual = virtual_group_by_id(target_group_id)
    if not virtual:
        raise RuntimeError("group not found")
    return add_virtual_group_client(target_group_id, client_id)


def set_device_wifi(ip, ssid, password):
    if not ip:
        raise RuntimeError("device heeft geen IP-adres")
    payload = json.dumps({"ssid": ssid, "password": password}).encode("utf-8")
    endpoints = [
        f"http://{ip}/api/wifi",
        f"http://{ip}/api/wifi/settings",
        f"http://{ip}/wifi",
    ]
    errors = []
    for endpoint in endpoints:
        request = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=4) as response:
                text = response.read().decode("utf-8", "replace")
                if 200 <= response.status < 300:
                    return {"endpoint": endpoint, "response": text}
                errors.append(f"{endpoint}: HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            errors.append(f"{endpoint}: HTTP {exc.code}")
        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")
    raise RuntimeError(
        "Deze ESP32-firmware lijkt Wi-Fi wijzigen via HTTP nog niet te ondersteunen. "
        "Flash/provision via USB of voeg een firmware-endpoint toe. Details: " + "; ".join(errors[-2:])
    )


def ping_host(ip):
    if not ip:
        return {"ok": False, "rtt_ms": None, "rtt_max_ms": None, "loss_percent": 100.0, "error": "no ip"}
    try:
        proc = subprocess.run(
            ["ping", "-c", "3", "-i", "0.2", "-W", "1", ip],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "rtt_ms": None, "rtt_max_ms": None, "loss_percent": 100.0, "error": str(exc)}

    loss_match = re.search(r"([0-9.]+)% packet loss", proc.stdout)
    rtt_match = re.search(r"rtt [^=]+ = ([0-9.]+)/([0-9.]+)/([0-9.]+)/", proc.stdout)
    loss_percent = float(loss_match.group(1)) if loss_match else (0.0 if proc.returncode == 0 else 100.0)
    return {
        "ok": loss_percent < 100,
        "rtt_ms": float(rtt_match.group(2)) if rtt_match else None,
        "rtt_max_ms": float(rtt_match.group(3)) if rtt_match else None,
        "loss_percent": loss_percent,
        "error": "" if proc.returncode == 0 else proc.stderr.strip() or proc.stdout.strip()[-160:],
    }


def process_up(pattern):
    try:
        proc = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, check=False)
        return proc.returncode == 0
    except FileNotFoundError:
        return False


def unit_active(unit):
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", "--quiet", unit],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return proc.returncode == 0
    except Exception:
        return False


def watchdog_active():
    if unit_active("snapcast-esp32-watchdog.timer") or unit_active("snapcast-esp32-watchdog.service"):
        return True
    if os.environ.get("ENABLE_ESP32_WATCHDOG", "1") != "0":
        if Path("/usr/local/bin/snapcast-esp32-watchdog.py").exists():
            return True
        return process_up("snapcast-esp32-watchdog")
    return False


def collect_metrics_once():
    item = {
        "ts": int(time.time()),
        "services": {
            "snapserver": process_up("snapserver"),
            "librespot": process_up("librespot"),
            "ffmpeg": process_up("ffmpeg"),
            "avahi": process_up("avahi-daemon"),
            "esp32-watchdog": watchdog_active(),
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
                    "rtt_max_ms": ping.get("rtt_max_ms"),
                    "loss_percent": ping.get("loss_percent"),
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
                clients = flatten_clients(status)
                self.send_json(
                    {
                        "ok": True,
                        "snapcast": status,
                        "dashboard_groups": dashboard_groups(status),
                        "clients": enrich_clients(clients, history),
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
                "esp32-watchdog": (LOG_DIR / "esp32-watchdog.log", "snapcast-esp32-watchdog.service"),
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
            elif action == "create_virtual_group":
                result = create_virtual_group(payload.get("name", "Nieuwe groep"))
            elif action == "delete_virtual_group":
                result = delete_virtual_group(payload["group_id"])
            elif action == "move_client_to_group":
                result = move_client_to_group(payload["client_id"], payload["group_id"])
            elif action == "add_group_client":
                result = add_virtual_group_client(payload["group_id"], payload["client_id"])
            elif action == "remove_group_client":
                result = remove_virtual_group_client(payload["group_id"], payload["client_id"])
            elif action == "activate_virtual_group":
                result = activate_virtual_group(payload["group_id"])
            elif action == "set_group_stream":
                result = rpc("Group.SetStream", {"id": payload["group_id"], "stream_id": payload["stream_id"]})
            elif action == "set_group_name":
                if str(payload["group_id"]).startswith("dash-"):
                    result = set_virtual_group_name(payload["group_id"], payload["name"])
                else:
                    result = rpc("Group.SetName", {"id": payload["group_id"], "name": payload["name"]})
            elif action == "set_client_name":
                result = rpc("Client.SetName", {"id": payload["client_id"], "name": payload["name"].strip()})
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
            elif action == "set_device_wifi":
                result = set_device_wifi(payload.get("ip", ""), payload.get("ssid", ""), payload.get("password", ""))
            else:
                self.send_json({"ok": False, "error": "unknown action"}, 400)
                return
            collect_metrics_once()
            self.send_json({"ok": True, "result": result})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=metrics_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", DASHBOARD_PORT), Handler)
    print(f"dashboard listening on 0.0.0.0:{DASHBOARD_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
