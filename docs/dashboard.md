# Dashboard

De Docker-container bevat een kleine webinterface op poort `8080`.

```text
http://<server-ip>:8080
```

Bijvoorbeeld:

```text
http://192.168.230.44:8080
```

## Overzicht

Het overzicht toont alle Snapcast clients die de server kent:

- naam en client-id
- IP-adres
- groep en stream
- laatste ping latency
- volume/mute
- ingestelde Snapcast latency

Volume, mute en latency kun je direct aanpassen.

## Groepen

In `Groepen` kun je clients aan een bestaande Snapcast groep koppelen en de stream van die groep kiezen.

Snapserver maakt groepen zelf aan op basis van bekende clients. Als een client niet zichtbaar is, start de ESP32 opnieuw of laat hem kort verbinden met de Snapserver.

## Kwaliteit

De grafieken zijn lichtgewicht metingen vanuit de container:

- ping latency naar de ESP32 IP-adressen
- verbonden/niet verbonden status volgens Snapserver
- service-status van `snapserver`, `librespot`, `ffmpeg`, `avahi` en de ESP32-watchdog

Korte pieken van honderden milliseconden zijn een sterke aanwijzing voor Wi-Fi stalls. Dat past bij haperingen die pas na een tijdje optreden.

## Logs

De container schrijft logs naar `/data/logs`:

- `snapserver.log`
- `librespot.log`
- `dashboard.log`
- `idle-mute.log`
- `esp32-watchdog.log`

Het dashboard toont de laatste regels van die bestanden. Voor volledige logs kun je nog steeds gebruiken:

```sh
docker compose logs -f spotify-whole-house
```
