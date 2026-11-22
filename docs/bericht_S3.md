# Bericht S3 – Belegprüfung aller Funde (L60, F2)

Stand: 22.11.2026, 09:00, Branch arbeit/S3, geprüfter Stand 354aaef. Rollenkette vor dem Code: docs/uebergabe.md.

**Kern-Check:** Punkte 1–6 eingehalten. Keine Regel, kein Fund und kein Status wurde verändert; data/raw wurde nur gelesen.

## Ergebnis

| Stufe | geprüft | bestanden | nicht bestanden |
|---|---|---|---|
| 1 (zuerst Nr. 1 und 2) | 22 | 22 | 0 |
| 2 | 378 | 378 | 0 |
| 3 | 137 | 137 | 0 |
| 4 | 58 | 58 | 0 |
| **gesamt** | **595** | **595** | **0 Fehlalarme** |

- Die App zeigt jetzt bei **1.706 von 1.706 Funden** „Beleg am Original geprüft“.
- data/qa/s2_ergebnis.json: 1.127 → 1.722 Einträge (595 neu, 0 geändert, 0 entfernt). Die 16 Einträge über 1.706 gehören zu Funden, die durch frühere Parser-Korrekturen entfallen sind.
- „Geprüft“ heißt: wörtlich im Block der eigenen Position gefunden. Es sagt nichts über die fachliche Richtigkeit; der Fehlalarm-Verdacht L56 bleibt.

## Methode (ohne parse())

- **GAEB XML:** Item der Rohdatei, Description und SubDescr; Einheit, Menge und Provis aus den Feldern.
- **GAEB 90:** nur die Sätze 21–30 der Position; Text aus Satz 25/26, Menge und Einheit aus Satz 21.
- **PDF:** Seitentext von der OZ-Zeile bis zur letzten Mengenzeile, dazu Unterbeschreibungen. Wiederkehrende Kopfzeilen beenden die Position nicht.

## Prüfung

- 36/36 Reihen auf 354aaef, Doppellauf 13/13, Durchlauf 43 OK, 1 Hinweis, 0 Fehler, test_skeptiker_s2 52/52.
- 1.706 Fund-IDs unverändert (Hash 87be325c697ebce4), Goldstandard 22/22, E11 44/44, data/findings leer.
- **Fehlschlag FS5:** Der erste Volllauf war 35/36, weil das Skript bei 22 Funden Nr. 1/2 ein leeres Feld schrieb. Das Skript wurde korrigiert, die Einträge neu erzeugt, der Test blieb unverändert.
- **Zeitrahmen:** 25 Minuten um etwa 8 Minuten überschritten (FS5).

## Kalkulator-Urteil [ANNAHME]

**Nützlich.** Ich kann jeden Beleg als wörtlich gefunden ansehen. Ob der Fund für mein Angebot zählt, entscheide weiter ich.

## Prioritäten-Auditor

Abgenommen. Kern-Check bestätigt.
