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

- `server/`: installatie- en configuratiebestanden voor de Linux server.
- `esp32/`: flashscripts, firmware-notities en de gebruikte ESP32-A1S binaries.
- `tools/`: kleine hulpscripts voor seriele logging en Snapcast controle.
- `docs/`: uitleg, troubleshooting en bekabeling.

## Huidige bewezen setup

- Server: Ubuntu/Debian LXC of kleine Linux machine.
- Spotify endpoint: `Spotify Whole House`.
- Server stream: `48000:16:2`, PCM, `chunk_ms=20`.
- Snapserver buffer: `6000 ms`.
- ESP32 client latency: `2000 ms`.
- ESP32-A1S board: AI Thinker / ES8388 audio codec.

## Snelle installatie

Op een verse Debian/Ubuntu server:

```sh
sudo ./server/install-server.sh
```

Daarna:

```sh
sudo systemctl status snapserver
sudo systemctl status librespot-snapcast
```

Kies in Spotify het apparaat `Spotify Whole House`.

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
