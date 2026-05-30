# Serverinstallatie

## Aanbevolen: Docker

Gebruik een Linux host met Docker en Docker Compose. De container draait op het hostnetwerk zodat Spotify Connect, Snapcast en mDNS discovery correct werken.

```sh
git clone https://github.com/Dominick-Vansevenant/esp32distriaudio.git
cd esp32distriaudio
docker compose up -d --build
```

Controleer:

```sh
docker compose ps
docker compose logs -f spotify-whole-house
```

Dashboard:

```text
http://<server-ip>:8080
```

Op de testserver is dat bijvoorbeeld:

```text
http://192.168.230.44:8080
```

Snapcast status:

```sh
printf '{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}\n' | nc -w 3 127.0.0.1 1705
```

Beide ESP32 clients activeren:

```sh
docker compose exec spotify-whole-house /tools/snapcast-activate-two-esp32.sh
```

## Avahi / mDNS

De container start standaard Avahi. Als je Docker host zelf al Avahi draait en er is een conflict op `5353/udp`, zet dan in `docker-compose.yml`:

```yaml
environment:
  ENABLE_AVAHI: "0"
```

Laat dan Avahi op de host draaien.

## Bare-metal alternatief

Gebruik Debian of Ubuntu. De testsetup draaide eerst op Ubuntu 24.04 in een LXC, maar dezelfde aanpak werkt op echte hardware.

```sh
git clone https://github.com/Dominick-Vansevenant/esp32distriaudio.git
cd esp32distriaudio
sudo ./server/install-server.sh
```

Services controleren:

```sh
systemctl status snapserver
systemctl status librespot-snapcast
systemctl status avahi-daemon
```

Snapcast status:

```sh
./tools/snapcast-status.sh
```

Beide ESP32 clients activeren:

```sh
sudo ./tools/snapcast-activate-two-esp32.sh
```

## Spotify

Open Spotify en kies `Spotify Whole House`.

Na herstart van de server kan Spotify enkele seconden nodig hebben om het apparaat opnieuw te tonen. Soms helpt het om in Spotify kort een ander device te kiezen en daarna opnieuw `Spotify Whole House`.
