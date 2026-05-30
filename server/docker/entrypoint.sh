#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  if [ -n "${LIBRESPOT_PID:-}" ]; then kill "$LIBRESPOT_PID" 2>/dev/null || true; fi
  if [ -n "${SNAPSERVER_PID:-}" ]; then kill "$SNAPSERVER_PID" 2>/dev/null || true; fi
  if [ -n "${IDLE_MUTE_PID:-}" ]; then kill "$IDLE_MUTE_PID" 2>/dev/null || true; fi
  if [ -n "${DASHBOARD_PID:-}" ]; then kill "$DASHBOARD_PID" 2>/dev/null || true; fi
  if [ -n "${AVAHI_PID:-}" ]; then kill "$AVAHI_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

if [ "${ENABLE_AVAHI:-1}" = "1" ]; then
  mkdir -p /run/dbus
  dbus-daemon --system --fork || true
  avahi-daemon --no-drop-root --daemonize || true
fi

mkdir -p /data/logs

/usr/local/bin/librespot-snapcast-wrapper.sh 2>&1 | tee -a /data/logs/librespot.log &
LIBRESPOT_PID=$!

sleep 1

snapserver --logging.sink=stdout --server.datadir=/data 2>&1 | tee -a /data/logs/snapserver.log &
SNAPSERVER_PID=$!

sleep 2

if [ "${ENABLE_IDLE_MUTE:-1}" = "1" ]; then
  /usr/local/bin/snapcast-idle-mute.py 2>&1 | tee -a /data/logs/idle-mute.log &
  IDLE_MUTE_PID=$!
fi

python3 /opt/esp32distriaudio-dashboard/app.py 2>&1 | tee -a /data/logs/dashboard.log &
DASHBOARD_PID=$!

wait -n "$SNAPSERVER_PID" "$LIBRESPOT_PID" "${IDLE_MUTE_PID:-$SNAPSERVER_PID}" "$DASHBOARD_PID"
