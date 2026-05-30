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
  iputils-ping \
  libasound2-dev \
  libssl-dev \
  netcat-openbsd \
  pkg-config \
  procps \
  python3 \
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
install -m 0755 server/snapcast-idle-mute.py /usr/local/bin/snapcast-idle-mute.py
install -m 0644 server/systemd/librespot-snapcast.service /etc/systemd/system/librespot-snapcast.service
install -m 0644 server/systemd/snapcast-idle-mute.service /etc/systemd/system/snapcast-idle-mute.service
mkdir -p /opt/esp32distriaudio/server /var/log/esp32distriaudio /var/lib/esp32distriaudio
cp -a server/dashboard /opt/esp32distriaudio/server/
install -m 0644 server/systemd/esp32distriaudio-dashboard.service /etc/systemd/system/esp32distriaudio-dashboard.service

cp -a /etc/snapserver.conf "/etc/snapserver.conf.bak.$(date +%Y%m%d-%H%M%S)"
python3 server/render-snapserver-conf.py /etc/snapserver.conf

systemctl daemon-reload
systemctl enable --now avahi-daemon.service
systemctl enable --now snapserver.service
systemctl enable --now librespot-snapcast.service
systemctl disable --now snapcast-idle-mute.service >/dev/null 2>&1 || true
systemctl enable --now esp32distriaudio-dashboard.service

echo "Done. Select 'Spotify Whole House' in Spotify. Dashboard: http://SERVER_IP:8080"
