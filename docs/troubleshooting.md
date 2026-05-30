# Troubleshooting

## Spotify Whole House verschijnt niet

Docker:

```sh
docker compose ps
docker compose logs -f spotify-whole-house
```

Bare-metal:

Controleer:

```sh
systemctl status librespot-snapcast
systemctl status avahi-daemon
```

Herstart eventueel:

```sh
sudo systemctl restart avahi-daemon
sudo systemctl restart librespot-snapcast
```

## Spotify speelt, maar geen geluid

Controleer of Snapserver de stream als `playing` ziet:

```sh
./tools/snapcast-status.sh
```

Bij Docker:

```sh
printf '{"id":1,"jsonrpc":"2.0","method":"Server.GetStatus"}\n' | nc -w 3 127.0.0.1 1705
```

Controleer of de clients niet gemute zijn en in de juiste groep zitten:

```sh
sudo ./tools/snapcast-activate-two-esp32.sh
```

Let op: `snapcast-idle-mute` mute de ESP32 clients automatisch wanneer Spotify idle/gepauzeerd is. Dat voorkomt getik/geruis bij pauze. Zodra Spotify weer `playing` is, worden de clients automatisch unmuted.

## Audio is te snel of distorted

Gebruik de audio-first ESP32 firmware in deze repo. De standaard ESP-AI-Thinker firmware gaf in de testsetup te snelle/distorted audio.

## Gehakkel

Kijk naar Wi-Fi jitter:

```sh
ping -c 20 <esp-ip>
```

In de testsetup was ESP1 stabieler dan ESP2. ESP2 had hoge jitter en Snapserver disconnects. Mogelijke fixes:

- ESP dichter bij het access point.
- Andere USB-voeding.
- Kortere of betere USB-kabel.
- Alleen 2.4 GHz SSID gebruiken.
- ESP2 ook exact dezelfde audio-first firmware geven.

## Server is herstart

Docker:

```sh
docker compose restart
docker compose exec spotify-whole-house /tools/snapcast-activate-two-esp32.sh
```

Bare-metal:

```sh
sudo systemctl restart avahi-daemon
sudo systemctl restart snapserver
sudo systemctl restart librespot-snapcast
sudo ./tools/snapcast-activate-two-esp32.sh
```
