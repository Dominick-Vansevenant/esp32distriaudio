param(
  [Parameter(Mandatory=$true)]
  [string]$Ip,

  [string]$Firmware = "stable-wifi-audio-esp-ai-thinker"
)

$ErrorActionPreference = "Stop"

$firmwareDir = Join-Path $PSScriptRoot "firmware\$Firmware"
$app = Join-Path $firmwareDir "snapclient.bin"

if (!(Test-Path $app)) {
  throw "Firmware file not found: $app"
}

$uri = "http://$Ip`:8032/"

Write-Host "Uploading $app to $uri"
& curl.exe --http1.0 -H "Expect:" --max-time 180 --data-binary "@$app" $uri

if ($LASTEXITCODE -ne 0) {
  throw "OTA upload failed with exit code $LASTEXITCODE"
}

Write-Host "OTA upload complete. The ESP32 should reboot automatically."
