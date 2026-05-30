# ESP32-A1S latency investigation

## What we measured

- Server-side ping to `192.168.230.60` before the patched firmware: no packet loss, but frequent spikes around 80-180 ms.
- Server-side ping to `192.168.230.60` after OTA with the patched firmware: 0% packet loss over 80 packets, average around 9 ms, max around 82 ms.
- Server-side ping to `192.168.230.61`: repeated full loss windows while Snapserver still remembered the client.
- The same LAN pings normal devices at a few milliseconds, so this is not normal wired LAN latency.
- Snapserver and librespot stayed active while the ESP32 clients showed the unstable behavior.

## Current mitigation

- Snapcast client latency is set to `8000 ms` for both ESP32 clients.
- Snapserver buffer is set to `12000 ms` to absorb occasional ESP32 radio stalls.
- Snapserver uses `codec=pcm` and `chunk_ms=80` for the Spotify pipe. This avoids FLAC decode work on the ESP32 and keeps the packet rate lower than the original 20 ms chunks.
- A server-side ESP32 watchdog closes stale Snapcast TCP sessions when Snapserver still sees a client as connected but the ESP32 IP is no longer reachable.
- The watchdog also closes duplicate Snapcast TCP sessions per ESP32 IP. After OTA/reconnect testing, one ESP had five concurrent Snapcast streams to the same IP.
- `ESP32-A1S-1` was updated successfully over the firmware OTA port `8032` using the patched application image.
- `ESP32-A1S-1` was configured to use static Snapserver host `192.168.230.44:1704` with mDNS discovery disabled.
- Isolation test: ping stalls still occurred while Snapserver was stopped, proving the remaining issue is below the Spotify/Snapserver layer.

## Firmware root-cause candidate

The ESP32 Snapclient firmware has a few settings that are risky for continuous 2.4 GHz audio streaming:

- Wi-Fi power save is not explicitly disabled in `wifi_interface.c`.
- The station bandwidth is forced to `WIFI_BW_HT40`, which is fragile on crowded 2.4 GHz channels.
- The ESP32 11n/AMPDU path can introduce bursty receive latency on weak or busy 2.4 GHz links. The current test variant disables AMPDU and temporarily forces 802.11g-only operation.
- The upstream AI Thinker config enables sample insertion. On the tested ESP32-A1S / ES8388 boards this correlated with fast/distorted playback.

Espressif documents that modem-sleep keeps the station associated but periodically powers down RF/PHY/BB, and that `WIFI_PS_NONE` disables modem-sleep to minimize real-time receive delay. Espressif also documents both HT20 and HT40 Wi-Fi bandwidth modes for ESP32 station operation.

The patch in `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch` changes the firmware to:

- disable Wi-Fi power save with `esp_wifi_set_ps(WIFI_PS_NONE)`;
- use 20 MHz Wi-Fi bandwidth with `WIFI_BW_HT20`;
- disable AMPDU TX/RX aggregation and force station mode to `WIFI_PROTOCOL_11G`;
- request maximum Wi-Fi TX power and disable reduced TX power config;
- stop Improv Wi-Fi provisioning after 10 seconds instead of 3 minutes;
- disable ESP-side mDNS advertising during normal audio runtime;
- keep ES8388-friendly I2S settings with MSB format and inverted BCLK;
- disable sample insertion so the player uses APLL clock tuning instead.

## Next validation

1. Build a new ESP-AI-Thinker firmware from the patched source.
2. Flash one ESP32 first and compare ping/jitter and audio hickups against the unpatched unit.
3. If it improves, update the second ESP32 over OTA when it is reachable.

## References

- ESP-IDF Wi-Fi Performance and Power Save: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi-driver/wifi-performance-and-power-save.html
- ESP-IDF Wi-Fi bandwidth modes: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi-driver/overview.html#wifi-bandwidth-mode
