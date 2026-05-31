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
- Wi-Fi power-save uitgeschakeld en periodiek opnieuw afgedwongen tijdens runtime.
- Wi-Fi bandbreedte op HT20 in plaats van HT40.
- Wi-Fi 802.11n blijft aan, maar op HT20 met kleinere AMPDU block-ack windows. Dit houdt de airtime en TCP-retransmit-kans lager dan 11g-only, zonder de brede HT40-modus.
- Wi-Fi en LwIP IRAM-optimalisatie ingeschakeld.
- Snapclient hard-resync minder agressief gemaakt, zodat de 12s Snapserver-buffer korte Wi-Fi stalls kan absorberen zonder I2S mute/reset.
- I2S MSB slot format ingeschakeld en BCLK inversie geforceerd voor dit board.
- Sample insertion uitgeschakeld, zodat de player APLL clock tuning gebruikt.

Deze variant is bedoeld om de lange 500-1700 ms Wi-Fi stalls verder te testen nadat de 11g-only variant en een vaste 12 Mbit/s TX-rate variant nog packet loss en haperingen gaven.

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
