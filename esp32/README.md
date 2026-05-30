# ESP32-A1S firmware

Deze setup gebruikt ESP32-A1S boards als Snapcast clients. De server blijft het Spotify Connect endpoint.

## Board

Geteste hardware:

- ESP32-A1S / AI Thinker Audio Kit
- ES8388 audio codec
- Wi-Fi op 2.4 GHz

## Werkende firmwarevariant

De binaries in `esp32/firmware/audio-first-esp-ai-thinker/` zijn gebaseerd op Sonocotta/Esparagus Snapclient voor ESP-AI-Thinker, met experimentele audio-first wijzigingen:

- AI Thinker / ES8388 board profile.
- I2S MSB slot format ingeschakeld.
- BCLK inversie geforceerd voor dit board.
- Harde Snapcast resync en sample-insert/delete correctie tijdelijk uitgeschakeld.

Deze variant was nodig omdat de standaardfirmware audio te snel/distorted liet klinken. Door de sync-correctie tijdelijk uit te schakelen werd het audiosignaal bruikbaar. Dit is dus praktisch werkend, maar nog geen perfecte upstream-ready patch.

## Flashen

Vanaf Windows PowerShell:

```powershell
.\esp32\flash-esp32-a1s.ps1 -Port COM5
```

Voor een tweede board:

```powershell
.\esp32\flash-esp32-a1s.ps1 -Port COM7
```

Gebruik de UART micro-USB poort van de ESP32-A1S.

## Wi-Fi

Na flashen moet de ESP32 op hetzelfde netwerk zitten als de server. Gebruik een 2.4 GHz SSID. In de testsetup was de ESP2 gevoeliger voor Wi-Fi jitter; dat gaf haperingen ondanks dat de server en Spotify in orde waren.
