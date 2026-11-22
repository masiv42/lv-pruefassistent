# Übergabe – aktueller Stand

## FREIGABE NÖTIG

| Nr | Frage | Vorschlag | Folge bei ja | Folge bei nein |
|---|---|---|---|---|
| F1 | Öffentliches Repo masiv42/lv-pruefassistent anlegen und pushen? Lokal gebaut aus arbeit/M7b, Prüfliste in docs/snapshot_anleitung.md | ja | Repo wird angelegt und gepusht | bleibt lokal |
| F2 | Dürfen die 44 Namen der Originaldateien und kurze LV-Zitate (je Datei höchstens 303 Zeichen) öffentlich stehen? Die Testreihen brauchen sie | ja, sonst Rückfrage an die Orga | Snapshot bleibt so | Namen und Zitate müssen vor dem Push ersetzt und alle Reihen neu geprüft werden |

## Stand

- **Block:** M7b: Abgabe-Repo für die öffentliche Abgabe neu gebaut, ohne s2_ergebnis.json, Bildschirmfotos und zwei Protokolle. Ohne die Datei 36/36 Reihen grün (3 Einzelprüfungen sichtbar übersprungen), mit der Datei 36/36. App-Code gegenüber main unverändert. Nichts gepusht, arbeit/M7b ist nur lokal.
- **Video:** Fund Nr. 1 in 8209.003_Leistungsverzeichnis_leer.X83, OZ 05.01.4, „Beleg am Original geprüft“; im Browser auf 8502 nach 0,5 s sichtbar (erster Aufruf), danach 0,2 s. „Frühere Entscheidung“ wurde in M2c mit auszug_a.pdf und auszug_b.pdf gezeigt (LV_13_ELT.pdf, S. 48–50, Fund Nr. 3, OZ 2.6..1).
- **Abweichung (gemeldet):** Die Demo-Probe lief auf Teamwunsch im Agenten-Browser auf 8501, AGENTS.md sieht dafür 8502 vor. Nur gelesen; data/findings und Erfahrungsdatenbank waren danach leer. Der Status-Schritt auf 8502 wurde von der Berechtigungsprüfung blockiert und nicht umgangen.
- **Team-Meldungen:** seit der Übernahme ist keine Fehlermeldung aus der Testliste eingegangen; data/findings ist leer.
- **Kern-Check:** Punkte 1–6 eingehalten.
- **Zahlen:** 4.293 Positionen, 1.706 Funde, davon 1.706 mit am Original bestätigtem Beleg.
- **Tests auf 354aaef:** 36/36 Reihen, Doppellauf 13/13, Durchlauf 43 OK, 1 Hinweis, 0 Fehler, Goldstandard 22/22, 1.706 Fund-IDs unverändert (Hash 87be325c697ebce4).
- **E11:** 44/44, 44 Dateien, data/raw schreibgeschützt. **E12 (4):** data/findings leer, keine Erfahrungsdatenbank.
- **Team-App:** 8501 aus `../Construction Hackathon main`, mit `LV_ERFAHRUNG_DB` im Hauptordner. Aufruf mit `http://127.0.0.1:8501`: Am 22.11. um 04:39 meldete das Team „nicht erreichbar“, die App antwortete aber mit 200; das Log zeigt HTTPS-Anfragen an den HTTP-Port.
- **Vor Demo und Abgabe:** Status in data/findings und data/erfahrung nach archiv/ verschieben (E12 (4)); das Team setzt die Demo-Status selbst.
- **Sitzung UI:** arbeitet auf arbeit/ui2. Paket 1 ist integriert; für Paket 2 entfallen die beiden Vorschläge, weil sie jetzt auf main sind. Neu für das Design: Seite `3_Nachtrag_und_Streitpunkte.py`, Kasten „Erfahrung“ und Begründungsfeld.

## Rollenkette E1 – Block M7b, öffentliches Abgabe-Repo (vor dem Code, 09:40)

- **Scope-Wächter:** Nur das Build-Skript, die Prüfskripte und, falls nötig, ein sauberes Überspringen fehlender Belegdaten in Tests. Keine Regel, kein Fund, kein Status; data/raw nur lesen. Es wird nichts angelegt und nichts gepusht.
- **Prioritäten-Auditor:** Abnahme nur, wenn s2_ergebnis.json und die Bildschirmfotos fehlen, App und alle Testreihen ohne sie nicht abstürzen, der README-Satz des Teams wörtlich steht und jede Datei gegen den vollständigen Originaltext gemessen ist. Größere Übernahmen werden ausgeschlossen oder gemeldet.
- **Kalkulator, Erwartung [ANNAHME]:** „Öffentlich darf nichts aus den echten LVs stehen. Ohne Belegdaten soll die App ehrlich ‚noch nicht geprüft‘ zeigen.“

## Rollenkette E1 – Block M7, Demo-Probe und Snapshot (vor dem ersten Schritt, 09:01)

- **Scope-Wächter:** Keine neue Funktion (E8). Demo-Probe auf 8501 nur lesend; Status setzt das Team selbst, der Agent prüft den Statusschritt nur auf 8502 mit Temp-Ablage (E12 (4)). Das Snapshot-Repo wird nur lokal gebaut; Anlegen und Push erst nach Teamfreigabe.
- **Prioritäten-Auditor:** Snapshot mit einem Commit, ohne data/raw, .env, demo/, data/findings, Erfahrungsdatenbank; ki_cache und jede Kopie von Originaldaten geprüft. Abnahme mit Prüfliste bis 10:15.
- **Kalkulator, Erwartung [ANNAHME]:** „Die Demo muss genau die Schritte zeigen, die wir erzählen, und jede genannte Zahl muss auf dem Bildschirm oder in der Quelle stehen.“

## Rollenkette E1 – Block S3, Belegprüfung aller Funde (vor dem Code, 04:45)

- **Scope-Wächter:** Nur src/skeptiker_s2.py, sein Test und Einträge in data/qa/s2_ergebnis.json. Keine Regel, kein Fund, kein Status wird geändert; data/raw nur lesen. Geprüft wird ohne parse() am Original. Nicht Bestandenes bleibt „noch nicht geprüft“ und wird als Fehlalarm gemeldet, nichts wird still entfernt.
- **Prioritäten-Auditor:** Reihenfolge Stufe 1 (zuerst Nr. 1 und 2), dann 2, 3, 4. Jeder Beleg muss im Block der eigenen Position stehen, jeder Feldwert am Original belegt sein; ein nicht prüfbarer Feldwert besteht nicht. Bestehende Einträge bleiben unverändert. Harte Grenze 05:45, Paket 2 der UI hat Vorrang.
- **Kalkulator, Erwartung [ANNAHME]:** „Zuerst müssen die Widersprüche belegt sein, die mich am meisten kosten. Was nicht bestätigt ist, soll so dastehen, statt grün zu werden.“
## Rollenkette E1 – Block I2, Integration UI Paket 2 (vor dem Code, 05:07)

- **Scope-Wächter:** Integriert wird genau arbeit/ui2 @ f22ca0b, nicht UI3/UI4 (74b712b, e21e709: Beleg als Bild), für die noch kein Teamauftrag vorliegt. Keine Regel, kein Fund, kein Status; data/raw nur lesen.
- **Prioritäten-Auditor:** Gleicher Nachweis wie I1: alle Reihen, Doppellauf, 1.706 Fund-IDs unverändert, E11, Browser über lv-app-agent. Danach 8501 neu starten und Health 200 melden. Vorrang vor S3.
- **Kalkulator, Erwartung [ANNAHME]:** „Ich will mit einem Klick starten und zwischen Fund und Position springen, ohne dass sich an den Funden etwas ändert.“

## Rollenkette E1 – Block I1, Integration UI Paket 1 (vor dem Code, 04:24)

- **Scope-Wächter:** Integriert wird genau arbeit/ui2 @ 6886019, nicht die neuere Spitze f22ca0b (Paket 2). Dazu nur die zwei Vorschläge aus docs/uebergabe_sitzung_UI2.md: info["tabelle"] in src/bericht.py und die Prüfzeile in src/test_seite_uebersicht.py. Keine Regel, kein Fund, kein Status, data/raw nur lesen.
- **Prioritäten-Auditor:** Abnahme nur mit allen Reihen, Doppellauf, 1.706 unveränderten Fund-IDs, E11 und Browser über lv-app-agent. info["tabelle"] muss nur lesend aus demselben parse()-Lauf kommen; pruefe_lv() ohne diesen Schlüssel bleibt je Datei byte-gleich zu main d8b16e5.
- **Kalkulator, Erwartung [ANNAHME]:** „Die neue Oberfläche darf anders aussehen, aber kein Fund, keine Reihenfolge und kein Beleg darf sich dadurch ändern.“

## Rollenkette E1 – Block M6 (vor dem ersten Schritt, 04:16)

- **Scope-Wächter:** M6 = Team-Meldungen beheben, Durchlauf und Doppellauf nach jedem Fix, pitch_zahlen.md auf Endzahlen; jede Zahl mit Quelle (R11). Keine neue Funktion. Feature-Stopp 06:00.
- **Prioritäten-Auditor:** Team-Meldungen vor Pitch-Zahlen (E3). Pitch-Zahlen nur aus den Logs des letzten vollständigen Laufs; „nicht verwenden“-Liste bleibt.
- **Kalkulator, Erwartung [ANNAHME]:** „Im Pitch will ich nur Zahlen hören, die ich nachprüfen kann, und auch, was das Tool nicht findet.“

## Rollenkette E1 – Block S2 (vor dem Code, 03:35)

- **Scope-Wächter:** Nur src/skeptiker_s2.py, sein Test und die Einträge der 31 Funde in data/qa/s2_ergebnis.json (30 neu aus B1p3, 7|HEM|6.4.1). Keine Regel, kein Fund, kein Status wird geändert; data/raw nur lesen. Geprüft wird ohne parse(); nicht Bestandenes wird als Fehlalarm gemeldet und nicht eingetragen.
- **Prioritäten-Auditor:** Abnahme nur, wenn jeder Textbeleg im Block der eigenen Position vor deren Ende steht, jeder Feldwert an der Mengenzeile belegt ist, bestehende Einträge außer 7|HEM|6.4.1 byte-gleich bleiben und ein zweiter Lauf nichts ändert. Zeitrahmen 25 Minuten, Goldstandard 22/22.
- **Kalkulator, Erwartung [ANNAHME]:** „Wenn dort ‚am Original geprüft‘ steht, will ich mich darauf verlassen können. Lieber ein ehrliches ‚nicht bestätigt‘ als ein grüner Haken ohne Prüfung.“

## Rollenkette E1 – M2-Paket (nachgetragen, Abweichung F1)

- **Scope-Wächter:** Nur Aufträge vom 23:55 und 01:25. Keine neue Regel, keine neuen Funde, keine Beträge, kein Score; KI und Erfahrung ändern keinen Fund.
- **Prioritäten-Auditor:** Reihenfolge M2 → M2b → M2c; je Block Tests positiv und negativ, ein gemeinsamer Fertig-Check vor dem Merge.
- **Kalkulator, Erwartung [ANNAHME]:** „Ich will eine Liste, was mich in der Ausführung Geld oder Streit kosten kann, und sehen, wie wir früher entschieden haben. Nichts davon darf mir einen Fund ausreden.“
- **Daten & Parser:** Parser unverändert; Sicht über alle Dateien 1.190 Zeilen.
- **Prüflogik:** Abschnitt B gegen den Katalog geprüft; Nr. 13 fällt heraus (L58).
- **Wirtschaftlichkeit & Kosten:** nur Zählungen, keine Geldwerte in Seite und Blatt.
- **Skeptiker:** 20 von 20 Stichproben aus 5 Dateien wörtlich im Original.
- **Oberfläche & Bericht:** Einfache Streamlit-Bausteine, zwei neue Blätter im Risikobericht.
- **Kalkulator, Urteil [ANNAHME]:** nützlich; Rauschen-Risiko Nr. 12 in Abschnitt B.
- **Prioritäten-Auditor:** inhaltlich abgenommen, Merge erst nach F1.

## Offene Punkte

- L49, L50, L55, L56, L57, L58, L59 in docs/luecken.md.
- pitch_zahlen.md: vollständiger Nachzug in M6.
- Worktree „Construction Hackathon B2“ (6389a16) bleibt eingetragen und unberührt.

## Nächster Schritt

Team: Status-Schritt der Demo proben, Testklicks danach nach archiv/ verschieben (E12 (4)), F1 und F2 beantworten. Danach Repo anlegen und M8 Bereitschaft.

## Prüfpunkte

| Zeit | fertig | offen | Zeitbedarf |
|---|---|---|---|
| 09:25 | M7: Demo-Probe, Drehbuch, Snapshot lokal mit 36/36 Reihen | F1, F2, Status-Schritt durch das Team | Anlegen 5 min nach Freigabe |
| 09:01 | S3 geprüft: 595 von 595, 36/36 Reihen | M7, Snapshot | Snapshot bereit bis 10:15 |
| 04:42 | UI Paket 1 und M6-Doku auf main, 35/35 Reihen, 1.706 Fund-IDs unverändert | Paket 2, L60 (F1), M7 | Paket 2 ca. 20 min nach Meldung |
| 04:20 | M2-Paket und S2 auf main; Pitch-Zahlen auf arbeit/M6 | L60 (F1), Team-Meldungen, Integration ui2, M7 | L60 45–60 min falls ja; Integration nach Meldung |
| 04:16 | M2-Paket auf main, S2: 31 von 31 am Original, alle Reihen grün | L60 (F1), M6, Integration ui2, M7 | Pitch-Zahlen 20 min; Integration nach Meldung |
| 03:25 | M2, M2b, M2c und README-Beschreibung auf arbeit/M2, 30/30 Reihen; Sitzung war etwa 01:36–03:10 unterbrochen | F1–F3, Merge, M6, M7, Integration UI | Merge 10 min, M6 bis 06:00 |
| 01:15 | M0, M1 (B1p3): 64 Positionen ergänzt, fremder Text entfernt, Unterbeschreibungen in PDF und XML, alle Reihen grün | Merge, M2-Paket, M6, M7 | M2 30 min |
| 00:12 | M0: Übernahme, alle Reihen grün, Goldstandard 22/22, E11 44/44, Team-App getrennt auf 8501 | B1p3; M1–M8 | B1p3 bis zu 105 min |
| 23:45 | B1p2 fertig und auf main (c7d6afb); B5 gebaut | B5-Abschluss, Debug-Phase, F3 | B5-Abschluss 15 min |
| 23:00 | B2-Integration a)–h) gebaut (Nr. 1–19 in App und Export, 1.688 Funde) | Doppellauf-Wiederholung, Doku, Merge | Integration-Rest 20 min |
