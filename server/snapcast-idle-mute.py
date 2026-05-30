#!/usr/bin/env python3
import json
import os
import socket
import time

HOST = os.environ.get("SNAPCAST_HOST", "127.0.0.1")
PORT = int(os.environ.get("SNAPCAST_PORT", "1705"))
STREAM_ID = os.environ.get("SNAPCAST_STREAM", "Spotify")
CLIENT_IDS = [
    value.strip()
    for value in os.environ.get(
        "SNAPCAST_CLIENTS",
        "70:4B:CA:25:53:C0,70:4B:CA:24:D7:B4",
    ).split(",")
    if value.strip()
]
POLL_SECONDS = float(os.environ.get("SNAPCAST_IDLE_MUTE_POLL", "2"))
VOLUME_PERCENT = int(os.environ.get("SNAPCAST_VOLUME", "100"))

request_id = 0


def request(method, params=None):
    global request_id
    request_id += 1
    payload = {"id": request_id, "jsonrpc": "2.0", "method": method}
    if params is not None:
        payload["params"] = params

    line = json.dumps(payload, separators=(",", ":")) + "\n"
    with socket.create_connection((HOST, PORT), timeout=3) as sock:
        sock.sendall(line.encode())
        sock.settimeout(3)
        chunks = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
            if b"\n" in data:
                break

    text = b"".join(chunks).decode(errors="replace").strip().splitlines()[0]
    return json.loads(text)


def spotify_state():
    status = request("Server.GetStatus")
    streams = status.get("result", {}).get("server", {}).get("streams", [])
    for stream in streams:
        if stream.get("id") == STREAM_ID:
            return stream.get("status", "unknown")
    return "unknown"


def set_muted(muted):
    for client_id in CLIENT_IDS:
        try:
            request(
                "Client.SetVolume",
                {
                    "id": client_id,
                    "volume": {"muted": muted, "percent": VOLUME_PERCENT},
                },
            )
        except Exception as exc:
            print(f"failed to set mute={muted} for {client_id}: {exc}", flush=True)


def main():
    last_muted = None
    print(
        f"watching Snapcast stream {STREAM_ID}; clients={','.join(CLIENT_IDS)}",
        flush=True,
    )
    while True:
        try:
            state = spotify_state()
            should_mute = state != "playing"
            if should_mute != last_muted:
                set_muted(should_mute)
                print(f"stream={state}; muted={should_mute}", flush=True)
                last_muted = should_mute
        except Exception as exc:
            print(f"watcher error: {exc}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
