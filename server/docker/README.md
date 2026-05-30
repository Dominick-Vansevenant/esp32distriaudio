# Docker server

This is the preferred server deployment for ESP32 Distri Audio.

The container runs:

- `librespot` as Spotify Connect endpoint `Spotify Whole House`
- `ffmpeg` to resample Spotify PCM from 44.1 kHz to 48 kHz
- `snapserver` to distribute FLAC-encoded audio to ESP32-A1S Snapcast clients
- a small dashboard on port `8080` for clients, groups, quality graphs, and logs
- optional `avahi-daemon` for mDNS discovery

## Start

```sh
docker compose up -d --build
```

The compose file uses `network_mode: host`. This is intentional: Spotify Connect, Snapcast, and mDNS discovery all work best on the host network.

## Dashboard

Open:

```text
http://<server-ip>:8080
```

The dashboard can:

- show Snapcast clients, IP addresses, groups, stream, volume sliders, mute, and latency
- add dashboard groups and drag clients into groups
- rename Snapcast clients and groups
- switch a group to another Snapcast stream
- show ping latency and connection state graphs
- show `snapserver`, `librespot`, dashboard, and idle-mute logs
- try Wi-Fi changes when the ESP32 firmware exposes an HTTP Wi-Fi endpoint

The dashboard stores virtual group names in the `/data` volume. It does not store Wi-Fi passwords after a request. It talks to Snapserver over the local JSON-RPC port inside the host-network container.

## ESP32 watchdog

The image also runs `snapcast-esp32-watchdog.py` by default. It detects ESP32 clients that are still marked as connected by Snapserver while their IP address is no longer reachable. After repeated failures it closes the stale Snapcast TCP session so the server state becomes honest and the client can reconnect if its Wi-Fi stack recovers.

Disable it with:

```yaml
environment:
  ENABLE_ESP32_WATCHDOG: "0"
```

Adjust the loop interval with `ESP32_WATCHDOG_INTERVAL`, in seconds.

## Status

```sh
docker compose logs -f
docker compose exec spotify-whole-house /tools/snapcast-status.sh
```

If the helper script is not in the image you can query Snapserver from the host:

```sh
printf '{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}\n' | nc -w 3 127.0.0.1 1705
```

## Avahi / mDNS

By default the container tries to start Avahi. If your Docker host already runs Avahi and port `5353/udp` conflicts, set:

```yaml
environment:
  ENABLE_AVAHI: "0"
```

Then run Avahi on the host instead.
