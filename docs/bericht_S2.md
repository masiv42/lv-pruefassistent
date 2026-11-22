# Bericht S2 – Belegprüfung der 31 Funde aus B1p3 (L57, F2)

Stand: 22.11.2026, Branch arbeit/S2. Rollenkette vor dem Code: docs/uebergabe.md (Commit 3be72f3).

**Kern-Check:** Punkte 1–6 eingehalten. Keine Regel, kein Fund und kein Status wurde verändert; data/raw wurde nur gelesen.

## Ergebnis

- **src/skeptiker_s2.py** prüft ohne parse() am PDF-Seitentext. parse() liefert nur die Liste der Ziel-Funde.
- **Textbelege** müssen im Block der eigenen Position stehen, von der OZ-Zeile bis zur letzten Mengenzeile, dazu Unterbeschreibungen.
- **Feldwerte** (Einheit, OZ) müssen an der Mengenzeile bzw. Position stehen.
- **31 von 31 Funden bestanden, 0 Fehlalarme.**
- **data/qa/s2_ergebnis.json:** 1.097 → 1.127 Einträge. 30 ergänzt, 7|HEM|6.4.1 mit den aktuellen 3 Belegen ersetzt, alle übrigen 1.096 Einträge unverändert und in gleicher Reihenfolge.

## Prüfung

- test_skeptiker_s2 32/32: positive und negative Fälle, darunter Beleg hinter der Mengenzeile, Beleg aus der Folgeposition, falsche Einheit, unbekannter Feldwert.
- Negativprobe am Original: der frühere Beleg „(VAG RETO-STOP oder gleichwertig)“ von HEM 06.04.1 (S. 128) besteht nicht.
- Browser (lv-app-agent, LV_09_Porenbetondach.pdf): Fund 6|9.2.0 zeigt „Beleg am Original geprüft“, keine Serverfehler.
- Vollständiger Lauf auf c21b00f: 31/31 Reihen, Doppellauf 13/13, Durchlauf 0 Fehler, Goldstandard 22/22, E11 44/44. Danach nur das Datum „Stand“ auf 2026-11-22 gesetzt (test_skeptiker_s2, test_bericht, test_pruefung_formal grün).
- **Grenze (L60):** Über alle Dateien sind 1.111 von 1.706 Funden am Original bestätigt, 595 nicht. Das betrifft ältere Funde außerhalb dieses Auftrags.
- Der Status „geprüft“ belegt die Wörtlichkeit, nicht die fachliche Richtigkeit. Der Fehlalarm-Verdacht LV_08 (L56) bleibt deshalb bestehen.

## Kalkulator-Urteil [ANNAHME]

**Nützlich.** „Am Original geprüft“ steht jetzt auch an den wieder gefundenen Positionen, und die Prüfung kann durchfallen.

## Prioritäten-Auditor

Abgenommen. Kern-Check bestätigt; L60 ist als offene Grenze gemeldet.
