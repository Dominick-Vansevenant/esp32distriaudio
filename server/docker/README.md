# Docker server

This is the preferred server deployment for ESP32 Distri Audio.

The container runs:

- `librespot` as Spotify Connect endpoint `Spotify Whole House`
- `ffmpeg` to resample Spotify PCM from 44.1 kHz to 48 kHz
- `snapserver` to distribute audio to ESP32-A1S Snapcast clients
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

- show Snapcast clients, IP addresses, groups, stream, volume, mute, and latency
- move clients into an existing Snapcast group
- switch a group to another Snapcast stream
- show ping latency and connection state graphs
- show `snapserver`, `librespot`, dashboard, and idle-mute logs

The dashboard stores no credentials. It talks to Snapserver over the local JSON-RPC port inside the host-network container.

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
