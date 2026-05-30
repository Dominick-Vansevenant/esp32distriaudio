$ErrorActionPreference = "Stop"

$ports = Get-CimInstance Win32_SerialPort |
  Select-Object DeviceID, Name, Description |
  Sort-Object DeviceID

if (!$ports) {
  Write-Host "No serial ports found."
  exit 0
}

$ports | Format-Table -AutoSize
