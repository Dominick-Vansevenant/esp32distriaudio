# Stable Wi-Fi/audio ESP-AI-Thinker firmware

Built by GitHub Actions from commit `ad7d4c7` using `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch`.

Changes versus the upstream ESP-AI-Thinker config:

- Wi-Fi power save disabled.
- Wi-Fi bandwidth forced to 20 MHz.
- Wi-Fi station protocol restricted to 802.11g/802.11n, with 802.11b disabled.
- Wi-Fi AMPDU aggregation enabled with smaller block-ack windows.
- ESP32 802.11 TX rate fixed at 12 Mbit/s OFDM for more stable TCP ACK timing.
- Wi-Fi and LwIP IRAM optimizations enabled.
- Snapclient hard-resync relaxed from 2 ms to 75 ms, and queue-empty no longer causes a hard resync unless the client is already late.
- Opus chunk sizing fixed so `chkInFrames` uses the decoded sample count when Snapserver bundles multiple Opus frames per chunk.
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
ec0b549b277e971c5f26cc2ee552b4f158b264b4026943a0ce6c9724a4f9604c  bootloader.bin
7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f  ota_data_initial.bin
f8a731f7f8f59c3826ea978062eedc49f822465de138718c794b5d7fce18abcf  partition-table.bin
2f74ce4c51fd376fc087daea2b1874522571207e5a7d7a2f8c52cca466961dd3  snapclient.bin
```
