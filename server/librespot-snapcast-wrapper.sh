#!/bin/sh
set -eu

FIFO=/tmp/snapfifo
rm -f "$FIFO"
mkfifo "$FIFO"

LIBRESPOT=/root/.cargo/bin/librespot
if [ ! -x "$LIBRESPOT" ]; then
  LIBRESPOT="$(command -v librespot)"
fi

"$LIBRESPOT" \
  --name "Spotify Whole House" \
  --device-type speaker \
  --group \
  --bitrate 320 \
  --backend pipe \
  --format S16 \
  --disable-audio-cache \
  --cache /var/cache/librespot \
  --system-cache /var/cache/librespot \
  --initial-volume 50 \
  | /usr/bin/ffmpeg -hide_banner -loglevel warning \
      -f s16le -ar 44100 -ac 2 -i pipe:0 \
      -f s16le -ar 48000 -ac 2 pipe:1 \
  > "$FIFO"
