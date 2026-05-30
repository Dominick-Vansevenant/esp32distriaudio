param(
  [Parameter(Mandatory=$true)]
  [string]$Ip,

  [string]$ServerHost = "192.168.230.44",

  [int]$ServerPort = 1704,

  [switch]$Restart
)

$ErrorActionPreference = "Stop"

function Set-EspParam($Name, $Value) {
  $encoded = [uri]::EscapeDataString([string]$Value)
  $uri = "http://$Ip/post?param=$Name&value=$encoded"
  $response = Invoke-WebRequest -Uri $uri -Method POST -TimeoutSec 5
  Write-Host "$Name=$Value -> $($response.StatusCode) $($response.Content)"
}

Set-EspParam "snapserver_host" $ServerHost
Set-EspParam "snapserver_port" $ServerPort
Set-EspParam "snapserver_use_mdns" 0

if ($Restart) {
  Set-EspParam "restart" 1
}
