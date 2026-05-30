# Architectuur

## Waarom een server nodig blijft

De ESP32-A1S is goed als goedkope audio-client, maar niet als centrale Spotify/Snapcast server. De server doet:

- Spotify Connect discovery en login via `librespot`.
- Audio decoding naar PCM.
- Resampling van 44.1 kHz naar 48 kHz via `ffmpeg`.
- FLAC-encoding en distributie naar meerdere clients via `snapserver`.
- Groepen, volumes, latency en buffering.

## Datastroom

```text
Spotify app
  -> librespot --backend pipe
  -> ffmpeg -f s16le -ar 44100 -ac 2 -> -ar 48000
  -> /tmp/snapfifo
  -> snapserver source Spotify (FLAC, 40 ms chunks)
  -> ESP32-A1S Snapcast clients
```

## Servergrootte

Een kleine Linux machine is genoeg. Aanbevolen:

- Raspberry Pi 3B+ of Pi 4 via Ethernet.
- Kleine thin client of mini-pc met Debian/Ubuntu.
- LXC/VM op Proxmox werkt ook.

Absolute minimum zoals Pi Zero 2 W kan werken, maar Ethernet en stabiele voeding zijn belangrijker dan ruwe CPU.

## Docker

Het serverdeel is beschikbaar als Docker Compose setup. Gebruik host networking:

```yaml
network_mode: host
```

Dat houdt Spotify Connect discovery, Snapcast poorten en mDNS het eenvoudigst en betrouwbaarst.
