# Bericht I1 – Integration UI Paket 1 (arbeit/ui2 @ 6886019)

Stand: 22.11.2026, 04:42, Branch arbeit/I1, geprüfter Code 9bb73e0. Rollenkette vor dem Code: docs/uebergabe.md (Commit c5c1225).

**Kern-Check:** Punkte 1–6 eingehalten. Keine Regel, kein Fund und kein Status wurde verändert; data/raw wurde nur gelesen.

## Ergebnis

- **Integriert:** genau 6886019 (Design-System, Positions-Explorer, Stil der Seiten, aktuelles LV bleibt beim Seitenwechsel erhalten). Die neuere Spitze f22ca0b (Paket 2) ist nicht enthalten.
- **Vorschlag 1:** `info["tabelle"]` in src/bericht.py, wörtlich aus docs/uebergabe_sitzung_UI2.md.
- **Vorschlag 2:** Prüfzeile Farbschema in src/test_seite_uebersicht.py.
- **Ergänzt:** die vier UI-Testreihen in src/alle_testreihen.py und AGENTS.md.
- **Mit im Merge:** die Doku aus M6 (Pitch-Zahlen, README, Drehbuch).

## Nachweis

| Prüfung | Ergebnis |
|---|---|
| Alle Reihen auf 9bb73e0 | 35/35 grün |
| Doppellauf | 13/13, drei Läufe byte-gleich |
| Durchlauf | 43 OK, 1 Hinweis, 0 Fehler, 1.706 Funde, 51 Bieterfragen |
| Fund-IDs gegen main d8b16e5 | 1.706 = 1.706, gleiche Reihenfolge, Hash 87be325c697ebce4 |
| `pruefe_lv()` ohne `tabelle`, Prüfstand, Zeitpunkt | in allen 43 Dateien byte-gleich zu main |
| `info["tabelle"]` | in allen 43 Dateien gleiche Positionen in gleicher Reihenfolge wie parse(), Kurz- und Langtext gleich, jede Fund-OZ enthalten |
| Goldstandard | 22 von 22 |
| E11 | 44/44, 44 Dateien, data/raw schreibgeschützt |
| E12 (4) | data/findings leer, keine Erfahrungsdatenbank im Projekt |
| Browser (lv-app-agent, LV_09) | alle 5 Seiten ohne Fehler, Status und LV bleiben beim Seitenwechsel, Status nur in der Temp-Ablage, keine Serverfehler |

## Kalkulator-Urteil [ANNAHME]

**Nützlich.** Die Positionsliste und der Kopf mit Zählungen machen das LV schneller lesbar, und die Funde sind dieselben wie vorher.

## Prioritäten-Auditor

Abgenommen. Kern-Check bestätigt.
