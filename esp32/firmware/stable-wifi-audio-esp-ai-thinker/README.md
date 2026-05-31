# Stable Wi-Fi/audio ESP-AI-Thinker firmware

Built by GitHub Actions from commit `fb4518d` using `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch`.

Changes versus the upstream ESP-AI-Thinker config:

- Wi-Fi power save disabled.
- Wi-Fi bandwidth forced to 20 MHz.
- Wi-Fi AMPDU aggregation disabled.
- Wi-Fi station protocol restricted to 802.11g only, with 802.11b and 802.11n disabled.
- Wi-Fi and LwIP IRAM optimizations enabled.
- Snapclient hard-resync relaxed from 2 ms to 75 ms, and queue-empty no longer causes a hard resync unless the client is already late.
- Wi-Fi TX power reduction disabled and max TX power requested.
- Improv provisioning stops after 10 seconds instead of 3 minutes.
- ESP32 mDNS advertising is disabled during normal audio runtime.
- Sample insertion disabled.
- I2S MSB format enabled.
- BCLK inversion enabled.

Flash offsets:

```text
0x1000   bootloader.bin
0x8000   partition-table.bin
0x1d000  ota_data_initial.bin
0x20000  snapclient.bin
```

SHA256:

```text
fd857384c79f21868620ec72906189be18c42befa4a9b542ad56dafc8fbfd6ee  bootloader.bin
7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f  ota_data_initial.bin
f8a731f7f8f59c3826ea978062eedc49f822465de138718c794b5d7fce18abcf  partition-table.bin
c3f3d5f8ffe0a0075e8dacc80f94049f276433127fd5b8f4665e7ac4120391c1  snapclient.bin
```
