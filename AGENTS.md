# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
`esp32distriaudio` is a Spotify "Whole House" multi-room audio system: a small Linux
**server** streams Spotify audio out to ESP32-A1S Snapcast **clients**. Only the
server side is runnable in this VM (the ESP32 firmware is a separate ESP-IDF/CI +
Windows-flashing toolchain and is not part of the server dev loop). The runtime chain is:

`librespot` (Spotify Connect endpoint) → `ffmpeg` (44.1→48 kHz PCM) → `/tmp/snapfifo` → `snapserver` → Snapcast clients, with a Python dashboard on port 8080.

### Services (all server-side)
- **snapserver** (apt, hub): control JSON-RPC on `1705`, stream on `1704`, HTTP on `1780`.
- **librespot** (built via `cargo`): advertises the "Spotify Whole House" Connect endpoint.
- **ffmpeg** (apt): resampler in the librespot pipe wrapper.
- **dashboard** (`server/dashboard/app.py`, Python stdlib only, no pip deps): web UI on `8080`, talks to snapserver:1705.
- **avahi-daemon** (apt, optional): mDNS discovery.
- Optional daemons: `snapcast-esp32-watchdog.py`, `snapcast-idle-mute.py`.

### Running services in this container (do NOT use systemd)
The repo ships `server/systemd/*.service` units and `server/install-server.sh`, but
those target bare-metal hosts. In this container **run the processes directly** (the
Docker `server/docker/entrypoint.sh` model), not via `systemctl`. Typical dev startup:

```sh
# one-time per boot: fifo + writable data dir
rm -f /tmp/snapfifo && mkfifo /tmp/snapfifo
sudo mkdir -p /data/logs /var/cache/librespot && sudo chown -R "$USER" /data /var/cache/librespot

# snapserver: default config path is /etc/snapserver.conf, so pass the repo config with -c
cp server/docker/snapserver.conf /tmp/snapserver.conf
snapserver -c /tmp/snapserver.conf --logging.sink=stdout --server.datadir=/data

# full Spotify pipeline (librespot -> ffmpeg -> /tmp/snapfifo); the wrapper recreates the fifo
server/librespot-snapcast-wrapper.sh

# dashboard (override LOG_DIR/state so it doesn't need the Docker /data layout)
SNAPCAST_HOST=127.0.0.1 SNAPCAST_PORT=1705 DASHBOARD_PORT=8080 LOG_DIR=/data/logs \
  python3 server/dashboard/app.py
```

### Non-obvious caveats
- **librespot must be built with `cargo install librespot --locked`.** Plain
  `cargo install librespot` (as in `server/docker/Dockerfile`) currently fails to
  compile because a semver-compatible `vergen-lib` patch breaks librespot 0.8.0's
  build script (`the trait bound Build: Add is not satisfied`). `--locked` pins the
  crate's tested dependency versions and builds cleanly. librespot 0.8.0 also needs
  `rustc >= 1.85` (`rustup update stable` if the toolchain is older).
- The librespot binary lands in `/usr/local/cargo/bin/librespot` (on `PATH`); the
  wrapper falls back to `command -v librespot`, so no change needed.
- **True end-to-end audio needs a Spotify Premium login and a real ESP32-A1S client.**
  For headless dev you don't need either: run a stand-in software client with
  `snapclient -h 127.0.0.1 -p 1704 --player file:filename=/tmp/snap-out.pcm` and it
  shows up in the dashboard as a connected client (audio stays idle until Spotify plays).
- The dashboard picks its state dir as `/data` if that dir exists, else
  `/var/lib/esp32distriaudio`; logs default to `/data/logs`. Override with
  `LOG_DIR` / `DASHBOARD_STATE_FILE`.
- `ffmpeg` may print harmless `libncursesw.so.6: no version information available`
  warnings when launched inside a tmux shell (LD path); it does not affect the pipe.

### Lint / test / build
There is **no automated test suite and no linter config** (the only CI,
`.github/workflows/build-esp32-firmware.yml`, builds ESP32 firmware in an ESP-IDF
container and is unrelated to the server). Validate server code with:
`python3 -m py_compile server/dashboard/app.py server/*.py tools/*.py` and
`bash -n server/*.sh server/docker/*.sh tools/*.sh`.
