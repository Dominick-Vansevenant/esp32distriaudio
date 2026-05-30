# Firmware patches

`esp-ai-thinker-stable-wifi-audio.patch` is intended for `sonocotta/esparagus-snapclient`.

Build it with the GitHub Actions workflow `Build patched ESP32-A1S firmware`, or manually:

```sh
git clone --recursive https://github.com/sonocotta/esparagus-snapclient.git upstream
cd upstream
git apply ../esp32/firmware/patches/esp-ai-thinker-stable-wifi-audio.patch
. "$IDF_PATH/export.sh"
cd snapclient
cp ../configs/sdkconfig.esp-ai-thinker sdkconfig
idf.py build
```

Flash offsets stay:

```text
0x1000   bootloader.bin
0x8000   partition-table.bin
0x1d000  ota_data_initial.bin
0x20000  snapclient.bin
```
