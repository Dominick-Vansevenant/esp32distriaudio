#!/usr/bin/env bash
set -euo pipefail

printf '{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}\n' | nc -w 3 127.0.0.1 1705
