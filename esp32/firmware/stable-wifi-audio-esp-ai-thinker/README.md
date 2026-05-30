# Stable Wi-Fi/audio ESP-AI-Thinker firmware

Built by GitHub Actions from commit `aaa1fe3` using `esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch`.

Changes versus the upstream ESP-AI-Thinker config:

- Wi-Fi power save disabled.
- Wi-Fi bandwidth forced to 20 MHz.
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
270e11aea542864544b70efba01dcb5fb48f320d45e9fa78d416eb943b8ba46f  bootloader.bin
7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f  ota_data_initial.bin
f8a731f7f8f59c3826ea978062eedc49f822465de138718c794b5d7fce18abcf  partition-table.bin
3f7528f79e243e4277f4362de255122222a986130db0f52b1d9a20ed8fe0faf7  snapclient.bin
```
