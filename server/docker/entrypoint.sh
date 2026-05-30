#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  if [ -n "${LIBRESPOT_PID:-}" ]; then kill "$LIBRESPOT_PID" 2>/dev/null || true; fi
  if [ -n "${SNAPSERVER_PID:-}" ]; then kill "$SNAPSERVER_PID" 2>/dev/null || true; fi
  if [ -n "${AVAHI_PID:-}" ]; then kill "$AVAHI_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

if [ "${ENABLE_AVAHI:-1}" = "1" ]; then
  mkdir -p /run/dbus
  dbus-daemon --system --fork || true
  avahi-daemon --no-drop-root --daemonize || true
fi

/usr/local/bin/librespot-snapcast-wrapper.sh &
LIBRESPOT_PID=$!

sleep 1

snapserver --logging.sink=stdout --server.datadir=/data &
SNAPSERVER_PID=$!

wait -n "$SNAPSERVER_PID" "$LIBRESPOT_PID"
