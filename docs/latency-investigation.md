# ESP32-A1S latency investigation

## What we measured

- Server-side ping to `192.168.230.60` before the patched firmware: no packet loss, but frequent spikes around 80-180 ms.
- Server-side ping to `192.168.230.60` after OTA with the patched firmware: 0% packet loss over 80 packets, average around 9 ms, max around 82 ms.
- Server-side ping to `192.168.230.61`: repeated full loss windows while Snapserver still remembered the client.
- The same LAN pings normal devices at a few milliseconds, so this is not normal wired LAN latency.
- Snapserver and librespot stayed active while the ESP32 clients showed the unstable behavior.

## Current mitigation

- Snapcast client latency is set to `3500 ms` for both ESP32 clients.
- Snapserver uses `codec=pcm` and `chunk_ms=80` for the Spotify pipe. This avoids FLAC decode work on the ESP32 and keeps the packet rate lower than the original 20 ms chunks.
- A server-side ESP32 watchdog closes stale Snapcast TCP sessions when Snapserver still sees a client as connected but the ESP32 IP is no longer reachable.
- `ESP32-A1S-1` was updated successfully over the firmware OTA port `8032` using the patched application image.

## Firmware root-cause candidate

The ESP32 Snapclient firmware has a few settings that are risky for continuous 2.4 GHz audio streaming:

- Wi-Fi power save is not explicitly disabled in `wifi_interface.c`.
- The station bandwidth is forced to `WIFI_BW_HT40`, which is fragile on crowded 2.4 GHz channels.
- The upstream AI Thinker config enables sample insertion. On the tested ESP32-A1S / ES8388 boards this correlated with fast/distorted playback.

Espressif documents that modem-sleep keeps the station associated but periodically powers down RF/PHY/BB, and that `WIFI_PS_NONE` disables modem-sleep to minimize real-time receive delay. Espressif also documents both HT20 and HT40 Wi-Fi bandwidth modes for ESP32 station operation.

The patch in `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch` changes the firmware to:

- disable Wi-Fi power save with `esp_wifi_set_ps(WIFI_PS_NONE)`;
- use 20 MHz Wi-Fi bandwidth with `WIFI_BW_HT20`;
- keep ES8388-friendly I2S settings with MSB format and inverted BCLK;
- disable sample insertion so the player uses APLL clock tuning instead.

## Next validation

1. Build a new ESP-AI-Thinker firmware from the patched source.
2. Flash one ESP32 first and compare ping/jitter and audio hickups against the unpatched unit.
3. If it improves, update the second ESP32 over OTA when it is reachable.

## References

- ESP-IDF Wi-Fi Performance and Power Save: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi-driver/wifi-performance-and-power-save.html
- ESP-IDF Wi-Fi bandwidth modes: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi-driver/overview.html#wifi-bandwidth-mode
