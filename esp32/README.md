# ESP32-A1S firmware

Deze setup gebruikt ESP32-A1S boards als Snapcast clients. De server blijft het Spotify Connect endpoint.

## Board

Geteste hardware:

- ESP32-A1S / AI Thinker Audio Kit
- ES8388 audio codec
- Wi-Fi op 2.4 GHz

## Werkende firmwarevariant

De standaardvariant staat in `esp32/firmware/stable-wifi-audio-esp-ai-thinker/`. Ze is gebaseerd op Sonocotta/Esparagus Snapclient voor ESP-AI-Thinker, met wijzigingen voor stabielere 2.4 GHz audio:

- AI Thinker / ES8388 board profile.
- Wi-Fi power-save uitgeschakeld.
- Wi-Fi bandbreedte op HT20 in plaats van HT40.
- Wi-Fi AMPDU aggregation uitgeschakeld en station protocol op 802.11g-only gezet om 11n block-ack latency-spikes te vermijden. Opus houdt de airtime laag genoeg voor 11g.
- Wi-Fi en LwIP IRAM-optimalisatie ingeschakeld.
- Snapclient hard-resync minder agressief gemaakt, zodat de 12s Snapserver-buffer korte Wi-Fi stalls kan absorberen zonder I2S mute/reset.
- HTTP `/status` endpoint toegevoegd voor runtime-diagnose: RSSI, Wi-Fi channel/protocol en heap.
- I2S MSB slot format ingeschakeld en BCLK inversie geforceerd voor dit board.
- Sample insertion uitgeschakeld, zodat de player APLL clock tuning gebruikt.

Deze variant verminderde de ping-jitter op `ESP32-A1S-1` duidelijk in de testsetup.

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

## OTA-update

Als de ESP32 al draait en poort `8032` bereikbaar is, kun je alleen de app via Wi-Fi updaten:

```powershell
.\esp32\ota-update-esp32-a1s.ps1 -Ip 192.168.230.60
```

De OTA-server op de ESP32 is eenvoudig. Het script gebruikt daarom HTTP/1.0 en schakelt `Expect: 100-continue` uit.

## Snapserver statisch instellen

Zet de ESP32 op een vaste Snapserver-host en schakel mDNS-discovery uit:

```powershell
.\esp32\configure-static-snapserver.ps1 -Ip 192.168.230.60 -ServerHost 192.168.230.44 -Restart
```

Dit vermindert onnodige discovery-activiteit en maakt reconnects voorspelbaarder.

## Wi-Fi

Na flashen moet de ESP32 op hetzelfde netwerk zitten als de server. Gebruik een 2.4 GHz SSID. In de testsetup was de ESP2 gevoeliger voor Wi-Fi jitter; dat gaf haperingen ondanks dat de server en Spotify in orde waren.
