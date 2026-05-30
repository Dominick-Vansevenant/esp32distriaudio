param(
  [Parameter(Mandatory=$true)]
  [string]$Port,

  [string]$Python = "",

  [string]$Firmware = "stable-wifi-audio-esp-ai-thinker"
)

$ErrorActionPreference = "Stop"

if (!$Python) {
  $bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  if (Test-Path $bundledPython) {
    $Python = $bundledPython
  } else {
    $Python = "python"
  }
}

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

& $Python -m esptool version | Out-Host

& $Python -m esptool --chip esp32 --port $Port --baud 460800 `
  --before default-reset --after hard-reset write-flash `
  --flash-mode dio --flash-size 4MB --flash-freq 80m `
  0x1000 $bootloader `
  0x8000 $partition `
  0x1d000 $ota `
  0x20000 $app

if ($LASTEXITCODE -ne 0) {
  throw "esptool failed with exit code $LASTEXITCODE"
}
