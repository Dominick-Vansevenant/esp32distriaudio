# Stable Wi-Fi/audio ESP-AI-Thinker firmware

Built by GitHub Actions from commit `5d95f58` using `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch`.

Changes versus the upstream ESP-AI-Thinker config:

- Wi-Fi power save disabled.
- Wi-Fi bandwidth forced to 20 MHz.
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
7f9ccebd10789714b30bf6b937f4dbcdb9c6aa49c8532068e03839a6c1aad0b6  bootloader.bin
7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f  ota_data_initial.bin
f8a731f7f8f59c3826ea978062eedc49f822465de138718c794b5d7fce18abcf  partition-table.bin
190f468b10b5eb1a5bf00f02070bbbacf64e7e9b34016fa12ef1208deea65d95  snapclient.bin
```
