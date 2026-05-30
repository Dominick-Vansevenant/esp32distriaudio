# ESP32 Distri Audio

Spotify Whole House audio met een kleine Linux server en ESP32-A1S audio clients.

De werkende architectuur:

```text
Spotify app
  -> Spotify Whole House (librespot op de server)
  -> ffmpeg resample naar 48 kHz PCM
  -> Snapserver
  -> ESP32-A1S Snapcast clients
  -> line-out / versterker / actieve speakers
```

## Wat dit project bevat

- `server/`: Docker- en bare-metal configuratiebestanden voor de Linux server.
- `esp32/`: flashscripts, firmware-notities en de gebruikte ESP32-A1S binaries.
- `tools/`: kleine hulpscripts voor seriele logging en Snapcast controle.
- `docs/`: uitleg, troubleshooting en bekabeling.

## Huidige bewezen setup

- Server: Docker op Ubuntu/Debian, een kleine Linux machine, of LXC/VM.
- Spotify endpoint: `Spotify Whole House`.
- Server stream: `48000:16:2`, PCM, `chunk_ms=20`.
- Snapserver buffer: `6000 ms`.
- ESP32 client latency: `2000 ms`.
- ESP32-A1S board: AI Thinker / ES8388 audio codec.

## Snelle installatie met Docker

Op een Linux server met Docker:

```sh
git clone https://github.com/Dominick-Vansevenant/esp32distriaudio.git
cd esp32distriaudio
docker compose up -d --build
```

Controleer:

```sh
docker compose ps
docker compose logs -f
```

Kies in Spotify het apparaat `Spotify Whole House`.

De container gebruikt `network_mode: host`. Dat is bewust zo, omdat Spotify Connect, Snapcast en mDNS discovery anders vaak niet betrouwbaar werken.

## Bare-metal alternatief

Wil je het zonder Docker installeren:

```sh
sudo ./server/install-server.sh
```

## ESP32 flashen

Sluit de ESP32-A1S via de UART micro-USB poort aan en flash vanaf Windows PowerShell:

```powershell
.\esp32\flash-esp32-a1s.ps1 -Port COM5
```

Voor een tweede board:

```powershell
.\esp32\flash-esp32-a1s.ps1 -Port COM7
```

Na flashen configureer je de Wi-Fi via de webinterface/provisioning van de firmware. De ESP32 moet dezelfde netwerklaag kunnen bereiken als de Snapserver.

## Belangrijk

De ESP32-A1S kan niet zelf betrouwbaar het serverdeel draaien. De server blijft nodig voor Spotify Connect, buffering, resampling en verdeling naar meerdere ESP32 clients.

Gebruik de `LOUT`/`ROUT` speaker outputs van de ESP32-A1S niet rechtstreeks op RCA line-in van actieve speakers. Gebruik bij voorkeur een echte line-out/headphone-out, of tap het line-level signaal voor de onboard versterker af. Zie `docs/cabling.md`.
