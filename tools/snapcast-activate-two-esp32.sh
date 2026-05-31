#!/usr/bin/env bash
set -euo pipefail

ESP1_ID="${ESP1_ID:-70:4B:CA:25:53:C0}"
ESP2_ID="${ESP2_ID:-70:4B:CA:24:D7:B4}"
GROUP_ID="${GROUP_ID:-78b1513c-6298-da56-af6b-ac4bbf586936}"

{
  printf '{"id":40,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":"%s","volume":{"muted":false,"percent":100}}}\n' "$ESP1_ID"
  sleep 0.2
  printf '{"id":41,"jsonrpc":"2.0","method":"Client.SetVolume","params":{"id":"%s","volume":{"muted":false,"percent":100}}}\n' "$ESP2_ID"
  sleep 0.2
  printf '{"id":42,"jsonrpc":"2.0","method":"Client.SetLatency","params":{"id":"%s","latency":12000}}\n' "$ESP1_ID"
  sleep 0.2
  printf '{"id":43,"jsonrpc":"2.0","method":"Client.SetLatency","params":{"id":"%s","latency":12000}}\n' "$ESP2_ID"
  sleep 0.2
  printf '{"id":44,"jsonrpc":"2.0","method":"Group.SetClients","params":{"id":"%s","clients":["%s","%s"]}}\n' "$GROUP_ID" "$ESP1_ID" "$ESP2_ID"
  sleep 0.2
  printf '{"id":45,"jsonrpc":"2.0","method":"Group.SetStream","params":{"id":"%s","stream_id":"Spotify"}}\n' "$GROUP_ID"
  sleep 0.2
  printf '{"id":46,"jsonrpc":"2.0","method":"Group.SetName","params":{"id":"%s","name":"ESP32-A1S Whole House"}}\n' "$GROUP_ID"
  sleep 0.2
  printf '{"id":47,"jsonrpc":"2.0","method":"Server.GetStatus"}\n'
} | nc -w 6 127.0.0.1 1705
