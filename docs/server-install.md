# Serverinstallatie

## 1. Besturingssysteem

Gebruik Debian of Ubuntu. De testsetup draaide op Ubuntu 24.04 in een LXC, maar dezelfde aanpak werkt op echte hardware.

## 2. Installatie uitvoeren

```sh
git clone https://github.com/Dominick-Vansevenant/esp32distriaudio.git
cd esp32distriaudio
sudo ./server/install-server.sh
```

## 3. Services controleren

```sh
systemctl status snapserver
systemctl status librespot-snapcast
systemctl status avahi-daemon
```

## 4. Snapcast status

```sh
./tools/snapcast-status.sh
```

## 5. Beide ESP32 clients activeren

Pas eventueel de client IDs in de environment aan. Standaard staan de geteste MAC-adressen in het script.

```sh
sudo ./tools/snapcast-activate-two-esp32.sh
```

## 6. Spotify

Open Spotify en kies `Spotify Whole House`.

Na herstart van de server kan Spotify enkele seconden nodig hebben om het apparaat opnieuw te tonen. Soms helpt het om in Spotify kort een ander device te kiezen en daarna opnieuw `Spotify Whole House`.
