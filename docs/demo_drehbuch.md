# Demo-Drehbuch (3–5 Minuten, aus Sicht eines Kalkulators)

Stand: 22.11.2026, 09:05, nach der Demo-Probe auf main (Sitzung B4). Die Seiten heißen in der App „LV-Prüfung“, „Übersicht“, „Positionen“, „Nachtragspotenzial und Streitpunkte“ und „Zuschlag und What-if“.

**Botschaft:** „Jeder Fund mit Beleg – immer dasselbe Ergebnis.“ Nicht die Gesamtzahl der Funde als Erfolg verkaufen. Viele Funde sind kein Qualitätsmerkmal; dass jeder Fund nachprüfbar ist, schon.

Zahlen nur aus `docs/pitch_zahlen.md`, genau mit dem dort genannten Bezug.

## Vorbereitung (vor der Demo, nicht live)

1. Sauberer Stand: Commit ohne „-dirty“ (Warnzeile im Risikobericht, B1r); E11-Prüfung 44/44.
2. Demo-LV erzeugen (nur Kopie, nie in data/raw): `python src/demo_lv.py "<Projekt>/data/raw" demo`. Das ergibt `demo/Demo-LV_B7_[PROJEKT_004].X83` mit je einem Fall pro Prüfung Nr. 1–19 an festen OZ (Liste in `demo/demo_faelle.json`).
3. KI-Antworten für das Demo-LV vorab in den Cache (L26, Sitzung B1); in der Demo nur aus dem Cache, kein Internet nötig.
4. App öffnen: `http://127.0.0.1:8501` (mit `http://`). data/findings und die Erfahrungsdatenbank vorher prüfen: Testklicks nach archiv/ verschieben, nicht löschen (E12 (4)).
5. Zweite Datei griffbereit: `GAEB-[PROJEKT_004].X83` aus data/raw (nur hochladen, nicht verändern).

## Ablauf

| Zeit | Klick / Handlung | Was zu sehen ist | Was gesagt wird (Zahl nur mit Quelle) |
|---|---|---|---|
| 0:00 | Startseite, kurz | Upload-Feld „GAEB XML, GAEB 90, PDF oder Excel“ | „Der Kalkulator bekommt ein LV in einem der drei Formate des Datensatzes: GAEB XML, GAEB 90, PDF.“ (pitch_zahlen: 3 Formate, 43 von 44 Dateien lesbar) |
| 0:20 | Demo-LV hochladen | Kopf: Datei, Format GAEB XML, Positionen, Prüfabdeckung; Fundliste sortiert nach Stufe, Rang, OZ | – |
| 0:40 | Seite „Übersicht“ | Vier Kacheln „1 – Fehlerprüfung“ … „4 – Unklarheit“ in den Stufenfarben; „Zuerst ansehen“ mit den ersten 5 Funden und wörtlichem Beleg; Diagramm Funde je Prüfung | „Zuerst kommt, was am sichersten und teuersten ist: Fehlerprüfung vor Kalkulationsrisiko vor Nachtragspotenzial vor Unklarheit.“ |
| 1:10 | Fund Nr. 1 an OZ 99.0001 öffnen | Kurztext „Druckrohr PE-HD DN 150“, Beleg aus dem Langtext „… DN 200 …“ wörtlich, Fundstelle | „Das Tool sagt nicht ‚Fehler‘, es zeigt beide Stellen wörtlich. Entscheiden tut der Kalkulator.“ |
| 1:40 | KI-Spalte zum Fund zeigen | KI-Vorschlag steht daneben; eine entwarnende Einordnung erscheint nur im Detail mit Warnhinweis; Stufe und Rang bleiben | „Die KI darf vorschlagen, aber nie entwarnen. In der Messung lag sie im ungünstigsten Fall bei 9 von 13 richtig, deshalb ändert sie nichts am Fund.“ (pitch_zahlen: 9 von 13) |
| 2:10 | Fund Nr. 9 an 99.0009 und Nr. 10 an 99.0010 | Risikohinweis „mögliches Nachtragspotenzial“, Beleg „… entsorgen“, „… vorhalten …“, Feldbeleg Einheit mWo | „Kein Urteil über Nachträge, nur der Hinweis, wo Kosten offen sind.“ |
| 2:40 | Status setzen: einen Fund „bestätigt“, einen „Rückfrage stellen“ | Zähler im Kopf ändern sich | „Der Mensch entscheidet; das Tool merkt sich die Entscheidung.“ |
| 3:00 | Dieselbe Datei **noch einmal** hochladen | Gleiche Funde, gleiche Reihenfolge, gleiche Fund-IDs; Status bleibt | „Gleiche Eingabe, gleiches Ergebnis. Drei Läufe byte-gleich.“ (pitch_zahlen: Doppellauf, alle Prüfungen: 3 Läufe byte-gleich) |
| 3:20 | Risikobericht herunterladen und öffnen | Übersicht „Für den Kalkulator“ / „Prüfstand (technisch)“; Blatt Funde mit Nr., Stufe als Text, Menge/EP/GP, Beleg; Blatt Legende | „Der Bericht ist das Arbeitsblatt für die Kalkulation, mit Beleg in jeder Zeile.“ |
| 3:50 | Bieterfragen herunterladen | Entwürfe nur zu Funden mit Empfehlung „Rückfrage stellen“, je mit OZ und wörtlichem Beleg; Hinweis „Entwurf … vor dem Versand prüfen“ | „Aus dem Fund wird eine sachliche Frage an den Auftraggeber, ohne rechtliche Bewertung.“ |
| 4:20 | Schluss (ohne Klick) | – | „Jeder Fund mit Beleg, immer dasselbe Ergebnis. Was das Tool nicht findet, sagt es auch: Im Rückblick an echten Nachträgen hätte es an 1 von 7 Stellen vorab gewarnt.“ (pitch_zahlen: Rückblick 1 von 7, Messung an einem LV) |

Optional, wenn Zeit bleibt (30 s): `GAEB-[PROJEKT_004].X83` aus dem Datensatz hochladen. Das zeigt, dass es auch mit echten Dateien geht; die Fundzahlen dieser Datei stehen in der Testliste (docs/testliste_team.md).

## Ergebnis der Probe (22.11.2026, 09:02, Stand b44436f)

- **Geprüft auf 8501, ohne Status zu setzen:** Upload des Demo-LV (71 Positionen, 52 Funde: Stufe 1: 7, 2: 9, 3: 21, 4: 15), Übersicht, Fund Nr. 1 an 99.0001 mit KI-Vorschlag aus dem Cache, Nr. 9 an 99.0009, Nr. 10 an 99.0010 mit „Einheit: mWo“, Positionen, Nachtragspotenzial und Streitpunkte (21 und 17), Zuschlag, erneuter Upload mit gleichen Zahlen. Keine Fehlermeldung.
- **Export (gleicher Code, ohne Browser):** Risikobericht mit 5 Blättern und 52 Fundzeilen, 7 Bieterfragen, alle 19 Demo-Fälle gefunden.
- **Status-Schritt 2:40:** In dieser Probe nicht geklickt, weil die Berechtigungsprüfung die Aktion blockiert hat und das Team die Status selbst setzt. Der Ablauf ist aus der Browser-Prüfung von Paket 2 belegt (8502, Temp-Ablage: „bestätigt 1“, bleibt beim Seitenwechsel); der App-Code ist seitdem unverändert. Bitte in der eigenen Probe einmal klicken.
- **Nicht im Browser geprüft:** das Herunterladen der beiden Excel-Dateien.
- **Beim Vorführen beachten:** Oben steht beim Demo-LV „52 von 52 Funden: Beleg noch nicht am Original geprüft“. Das ist richtig, weil das Demo-LV nicht zum Datensatz gehört. Dazu sagen: „Das ist unsere Testdatei; im Datensatz sind alle 1.706 Belege automatisch im Original wiedergefunden.“
- **Fensterbreite:** Bei schmalem Fenster werden die Knöpfe „Bestätigen“, „Verwerfen“ und „Rückfrage stellen“ abgeschnitten. Für die Aufnahme das Fenster breit ziehen.

## Was nicht gesagt wird

- Keine Zeitersparnis, keine Trefferquote, kein „findet alle Fehler“ (R11; pitch_zahlen „Nicht verwenden“).
- Keine Aussage zu Ansprüchen, nur „mögliches Nachtragspotenzial“ bzw. „möglicher Streitpunkt in der Ausführung“ (R7).
- Keine Geldbeträge als Risiko. Wenn auf der Übersicht „Positionswert laut LV (Summe GP)“ steht (nur bei bepreisten LVs): „Das ist der Wert der Positionen laut LV, kein Risikobetrag.“
- Die Gesamtzahl der Funde (1.706 im Datensatz) nicht als Erfolg nennen; wenn danach gefragt wird: „Das sind Hinweise zur Prüfung, jeder mit Beleg; viele davon sind nur Hinweise in Stufe 4.“

## Wenn etwas schiefgeht

- PDF lädt lange: Demo mit dem Demo-LV (GAEB XML, schnell) weiterführen, kein großes PDF live.
- KI nicht erreichbar: ohne Folgen, die Antworten kommen aus dem Cache; fehlt ein Cache-Eintrag, steht „noch nicht KI-geprüft“, und der Regel-Fund bleibt unverändert.
- Warnzeile „-dirty“ im Bericht: nicht vorführen; vorher sauberen Stand starten.
