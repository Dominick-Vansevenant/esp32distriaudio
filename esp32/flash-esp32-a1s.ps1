param(
  [Parameter(Mandatory=$true)]
  [string]$Port,

  [string]$Python = "python",

  [string]$Firmware = "stable-wifi-audio-esp-ai-thinker"
)

$ErrorActionPreference = "Stop"

$firmwareDir = Join-Path $PSScriptRoot "firmware\$Firmware"

$bootloader = Join-Path $firmwareDir "bootloader.bin"
$partition = Join-Path $firmwareDir "partition-table.bin"
$ota = Join-Path $firmwareDir "ota_data_initial.bin"
$app = Join-Path $firmwareDir "snapclient.bin"

foreach ($file in @($bootloader, $partition, $ota, $app)) {
  if (!(Test-Path $file)) {
    throw "Firmware file not found: $file"
  }
}

& $Python -m esptool --chip esp32 --port $Port --baud 460800 `
  --before default_reset --after hard_reset write_flash `
  --flash_mode dio --flash_size 4MB --flash_freq 80m `
  0x1000 $bootloader `
  0x8000 $partition `
  0x1d000 $ota `
  0x20000 $app
