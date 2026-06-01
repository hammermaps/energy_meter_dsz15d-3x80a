# Hardware, Verschaltung und Materialliste

## Ziel

Die beiden Impulsausgaenge `S0` und `S1` des Eltako DSZ15D-3x80A werden jeweils ueber eine identische NPN-Transistorstufe an einen GPIO des Raspberry Pi angeschlossen. Dadurch sieht der Raspberry Pi ausschliesslich ein sauberes 3,3-V-Signal.

## Verschaltungsplan je Impulskanal

```text
Eltako Sx+  ----[10 kOhm]----B   BC547B / 2N3904
                               \
Eltako Sx-  ---------------------E---------------- Raspberry Pi GND
                               /
GPIO BCM17/27 ----[1 kOhm]-----C----+----[10 kOhm]---- Raspberry Pi 3V3
                                     |
                                     +---- Raspberry Pi GPIO Eingang
                                     |
                                     +----[100 nF optional]---- Raspberry Pi GND

zusätzlich:
Basis (B) ----[100 kOhm]---- Emitter (E)
```

### Funktion

- `10 kOhm` an der Basis begrenzt den Basisstrom.
- `100 kOhm` zwischen Basis und Emitter zieht den Transistor sicher auf `LOW`, wenn kein Impuls anliegt.
- `10 kOhm` Pull-Up erzeugt ein sauberes `3,3 V` Pegel-Signal am GPIO.
- `1 kOhm` in Serie zum GPIO begrenzt Fehlerstroeme und schuetzt den Raspberry Pi.
- `100 nF` ist optional und filtert sehr kurze Stoerspitzen; die eigentliche Entprellung erfolgt in Software ueber `bounce_ms`.

## Gesamtverschaltung

```text
Eltako S0+ ---- NPN-Stufe Kanal 1 ---- Raspberry Pi GPIO17
Eltako S0- --------------------------- Raspberry Pi GND

Eltako S1+ ---- NPN-Stufe Kanal 2 ---- Raspberry Pi GPIO27
Eltako S1- --------------------------- Raspberry Pi GND

Raspberry Pi 3V3 ---- Pull-Up Widerstand Kanal 1
Raspberry Pi 3V3 ---- Pull-Up Widerstand Kanal 2
```

## Materialliste

| Menge | Bauteil | Hinweis |
| ---: | --- | --- |
| 1 | Raspberry Pi mit Raspberry Pi OS | z. B. Pi 3B oder neuer |
| 1 | 5-V-Netzteil fuer Raspberry Pi | stabil, passend zum Modell |
| 2 | BC547B oder 2N3904 | je einer fuer S0 und S1 |
| 2 | 10 kOhm Widerstand | Basiswiderstand |
| 2 | 100 kOhm Widerstand | Basis-Emitter Pulldown |
| 2 | 10 kOhm Widerstand | Pull-Up nach 3,3 V |
| 2 | 1 kOhm Widerstand | Serienwiderstand vor GPIO |
| 2 | 100 nF Keramikkondensator | optional gegen Stoerspitzen |
| 1 | Schraubklemmen / Hutschienenadapter | fuer saubere Verdrahtung |
| 1 | Gehaeuse | Beruehrungsschutz |
| 1 | Verbindungskabel | Litze / Dupont je nach Aufbau |

## Sicherheitshinweise

- Niemals `5 V` oder fremde Potentiale direkt auf einen GPIO legen.
- Raspberry Pi und Eltako muessen fuer diese NPN-Schaltung eine gemeinsame Masse haben.
- Wenn galvanische Trennung gefordert ist, statt der NPN-Stufe Optokoppler einsetzen.
- Verdrahtung nur spannungsfrei ausfuehren.
