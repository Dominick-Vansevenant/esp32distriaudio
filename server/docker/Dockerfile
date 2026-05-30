FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    avahi-daemon \
    build-essential \
    ca-certificates \
    curl \
    dbus \
    ffmpeg \
    libasound2-dev \
    libssl-dev \
    netcat-openbsd \
    pkg-config \
    snapserver \
  && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --profile minimal \
  && /root/.cargo/bin/cargo install librespot \
  && rm -rf /root/.cargo/registry /root/.cargo/git

COPY server/librespot-snapcast-wrapper.sh /usr/local/bin/librespot-snapcast-wrapper.sh
COPY server/docker/entrypoint.sh /usr/local/bin/esp32distriaudio-entrypoint.sh
COPY server/docker/snapserver.conf /etc/snapserver.conf
COPY tools /tools

RUN chmod +x /usr/local/bin/librespot-snapcast-wrapper.sh /usr/local/bin/esp32distriaudio-entrypoint.sh \
  && chmod +x /tools/*.sh \
  && mkdir -p /data /var/cache/librespot

EXPOSE 1704 1705 1780 5353/udp

ENTRYPOINT ["/usr/local/bin/esp32distriaudio-entrypoint.sh"]
