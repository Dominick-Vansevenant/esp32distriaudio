# Troubleshooting

## Spotify Whole House verschijnt niet

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

Controleer of de clients niet gemute zijn en in de juiste groep zitten:

```sh
sudo ./tools/snapcast-activate-two-esp32.sh
```

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

Na reboot:

```sh
sudo systemctl restart avahi-daemon
sudo systemctl restart snapserver
sudo systemctl restart librespot-snapcast
sudo ./tools/snapcast-activate-two-esp32.sh
```
