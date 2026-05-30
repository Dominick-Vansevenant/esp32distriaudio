# Bekabeling

## Actieve speakers met RCA line-in

Gebruik bij voorkeur een echte line-out of headphone-out van de ESP32-A1S:

```text
3.5 mm stereo jack -> 2x RCA male
```

- Rode RCA: rechts.
- Witte of zwarte RCA: links.

## LOUT / ROUT op ESP32-A1S

Op veel ESP32-A1S Audio Kit boards zijn `LOUT` en `ROUT` speaker outputs van de onboard versterker. Die zijn bedoeld voor passieve speakertjes, niet voor RCA line-in.

Sluit versterkte speaker outputs niet rechtstreeks aan op een line input. Dat kan vervormen en mogelijk de input beschadigen.

Veilige opties:

- Gebruik een echte line-out/headphone-out.
- Tap het line-level signaal af voor de onboard versterker.
- Gebruik een speaker-to-line level attenuator.

## Passieve speakers

Voor passieve speakers heb je een versterker nodig. De ESP32-A1S levert geen Sonos-achtig vermogen of DSP op zichzelf.
