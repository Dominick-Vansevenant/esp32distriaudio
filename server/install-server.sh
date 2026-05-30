#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root, for example: sudo ./server/install-server.sh" >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  avahi-daemon \
  build-essential \
  curl \
  ffmpeg \
  git \
  libasound2-dev \
  libssl-dev \
  netcat-openbsd \
  pkg-config \
  snapserver

if ! command -v cargo >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  # shellcheck source=/dev/null
  . "$HOME/.cargo/env"
fi

if ! command -v librespot >/dev/null 2>&1 && [ ! -x /root/.cargo/bin/librespot ]; then
  cargo install librespot
fi

install -m 0755 server/librespot-snapcast-wrapper.sh /usr/local/bin/librespot-snapcast-wrapper.sh
install -m 0644 server/systemd/librespot-snapcast.service /etc/systemd/system/librespot-snapcast.service

cp -a /etc/snapserver.conf "/etc/snapserver.conf.bak.$(date +%Y%m%d-%H%M%S)"
python3 server/render-snapserver-conf.py /etc/snapserver.conf

systemctl daemon-reload
systemctl enable --now avahi-daemon.service
systemctl enable --now snapserver.service
systemctl enable --now librespot-snapcast.service

echo "Done. Select 'Spotify Whole House' in Spotify."
