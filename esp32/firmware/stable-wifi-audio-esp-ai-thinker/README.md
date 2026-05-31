# Stable Wi-Fi/audio ESP-AI-Thinker firmware

Built by GitHub Actions from commit `a60ba37` using `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch`.

Changes versus the upstream ESP-AI-Thinker config:

- Wi-Fi power save disabled before and after Wi-Fi start, then reasserted periodically at runtime.
- Wi-Fi bandwidth forced to 20 MHz.
- Wi-Fi station protocol restricted to 802.11g/802.11n, with 802.11b disabled.
- Wi-Fi AMPDU aggregation enabled with smaller block-ack windows.
- Wi-Fi and LwIP IRAM optimizations enabled.
- Snapclient hard-resync relaxed from 2 ms to 75 ms, and queue-empty no longer causes a hard resync unless the client is already late.
- Opus chunk sizing fixed so `chkInFrames` uses the decoded sample count when Snapserver bundles multiple Opus frames per chunk.
- Wi-Fi TX power reduction disabled and max TX power requested.
- Improv provisioning stops after 10 seconds instead of 3 minutes.
- ESP32 mDNS advertising is disabled during normal audio runtime.
- Sample insertion disabled.
- I2S MSB format enabled.
- BCLK inversion enabled.
- Wi-Fi diagnostics endpoint exposed at `/wifi-status`.

Flash offsets:

```text
0x1000   bootloader.bin
0x8000   partition-table.bin
0x1d000  ota_data_initial.bin
0x20000  snapclient.bin
```

SHA256:

```text
ad4c8d4ea36ccfb61e623914ceda2b3f600224206f1d8b9f226e2268f7fef137  bootloader.bin
7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f  ota_data_initial.bin
f8a731f7f8f59c3826ea978062eedc49f822465de138718c794b5d7fce18abcf  partition-table.bin
30a6fdc74f78b6456149da8374f585131e07c0438640ed6c0d03f0322fa1b844  snapclient.bin
```
