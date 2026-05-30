# Audio-first ESP-AI-Thinker firmware

Flash offsets:

```text
0x1000   bootloader.bin
0x8000   partition-table.bin
0x1d000  ota_data_initial.bin
0x20000  snapclient.bin
```

SHA256:

```text
cf7e7453714b346bba001c2ff5078a116ad02229a89b4d994681931bfb66faf1  bootloader.bin
7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f  ota_data_initial.bin
f8a731f7f8f59c3826ea978062eedc49f822465de138718c794b5d7fce18abcf  partition-table.bin
fd965e56dbe22f6ec1680e0ac5468a05933e10212af88cb239d416f87f0c6e48  snapclient.bin
```

These binaries are experimental and tailored for the tested ESP32-A1S / ESP-AI-Thinker ES8388 boards.
