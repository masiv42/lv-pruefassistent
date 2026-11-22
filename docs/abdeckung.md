# Abdeckung der Challenge – Soll-Ist (B0b.1)

Stand: 21.11.2026, B1b (Nr. 1–6 nach E2). Soll: input/challenge_A_offiziell.md und input/pruefkatalog.md.
Status: **fertig** = umgesetzt und Standard E2 erfüllt · **Light** = bewusst reduziert, nur wenn Daten
fehlen, mit Begründung (E2) · **offen** = nicht oder noch nicht nach E2 umgesetzt.
Hinweis: Nr. 1–6 erfüllen seit B1b Standard E2 (docs/bericht_B1b.md); offene F-Fragen zu Nr. 1 und 3 sind
vermerkt (L34, L40, L41).

## Challenge-Text

| Punkt | Prüfung/Feature | Status | Beleg (Datei, Test, Commit) | Backlog-ID |
|---|---|---|---|---|
| Problem: lange LVs mit tausenden Positionen | Parser GAEB XML, GAEB 90, PDF; 43 von 44 Dateien lesbar (LV-Positionen.docx nicht); PDF seit B1p: Langtext nur aus dem Text der Position, seit B1p3 mit Positionsgrenze an der Mengenzeile, Unterbeschreibungen, OZ „1.2..2“ und Mengenzeilen ohne Einheit; 4.293 Positionen (src/test_parser_pdf.py, docs/bericht_B1p3.md) | fertig | src/lv_parser.py, src/validate_parser.py, docs/acceptance.md T1; e4fe05e | – |
| Problem: Risiken erkennen | Risikohinweise Nr. 5, 6 (Stufe 2, in der App gruppiert) | fertig | src/pruefung_formal.py, src/test_pruefung_formal.py, docs/bericht_B1b.md; B1b | B1b |
| Problem: aus früheren Projekten lernen | historische Projektdaten = bepreiste Dateien und Nachträge im Datensatz (T2) | offen | docs/decisions.md „B0b: T2“ | B3, B6 |
| Problem: Tippfehler | Prüfung Tippfehler (KI) | KI-Vorschlag, umgesetzt (B5; src/ki_b5.py, App-Aufklapper; Messung data/qa/b5_messung.json) | test_ki_b5.py 16/16 | B5 |
| Problem: Rechenfehler | Nr. 17 Rechenprüfung Menge × EP (1.242 Positionen nachgerechnet, 0 Abweichungen) | fertig | src/pruefung_rechnung.py, src/test_pruefung_rechnung.py, docs/bericht_B1e.md | B1e |
| Problem: übersehenes Nachtragspotenzial | Nr. 7–10 | offen | input/pruefkatalog.md | B2 |
| Goal: Import PDF | Parser PDF | fertig | src/lv_parser.py; docs/acceptance.md T1 | – |
| Goal: Import GAEB | Parser GAEB XML (X83/X84) und GAEB 90 (D83/D84/D86) | fertig | src/lv_parser.py; src/validate_parser.py | – |
| Goal: Import Excel | Excel-Import mit Spalten-Zuordnung | fertig (ohne Orga-Beispiel getestet, so gekennzeichnet) | src/excel_import.py, src/test_excel_import.py; Upload-Weiche in App und bericht.pruefe_lv | B4 |
| Goal: Fehler – missing items | mögliche fehlende Leistung (höchstens 5 Paarregeln, Risikohinweis) | fertig (Nr. 19, 5 Paarregeln, Risikohinweis) | src/pruefung_vollstaendigkeit.py, src/test_pruefung_vollstaendigkeit.py | B3 |
| Goal: Fehler – unclear descriptions | Nr. 11–14 Unklarheiten | fertig (Nr. 11–14) | src/pruefung_hinweise.py | B2b |
| Goal: Fehler – contradictions (in der Position) | Nr. 1, 2 Kurztext ≠ Langtext; KI-Gegenprüfung; Prüfabdeckung zeigt Positionen ohne eigenen Langtext | fertig (Fehlalarme Nr. 1 gemeldet, L41) | src/pruefung_widerspruch.py, src/test_pruefung.py, src/ki_pruefung.py, docs/bericht_B1b.md; B1b | B1b, B5 |
| Goal: Fehler – contradictions (zwischen Positionen) | Widersprüche zwischen Positionen (KI) | KI-Vorschlag, umgesetzt (B5; src/ki_b5.py, App-Aufklapper; Messung data/qa/b5_messung.json); Paare per Regel-Vorauswahl | test_ki_b5.py 16/16 | B5 |
| Goal: Fehler – typos | Tippfehler (KI) | KI-Vorschlag, umgesetzt (B5; src/ki_b5.py, App-Aufklapper; Messung data/qa/b5_messung.json) | test_ki_b5.py 16/16 | B5 |
| Goal: Risiko – imprecise scope | Nr. 11, 12 (vage nur in Kombination) | fertig (Nr. 11, 12) | src/pruefung_hinweise.py | B2b |
| Goal: Risiko – unusual quantities | Nr. 18 | fertig (Nr. 18; große Vorhaltemengen offen, B2-L7) | src/pruefung_hinweise.py | B2c |
| Goal: Nachtragspotenzial und Streitpunkte | Nr. 7–10 („mögliches Nachtragspotenzial“, R7) | fertig (Nr. 7–10, „mögliches Nachtragspotenzial“, R7) | src/pruefung_hinweise.py | B2a |
| Goal (optional): EP oder Zuschläge aus historischen Daten | Vergleichspreise aus bepreisten Dateien mit Quelle (T1); Zuschläge nur als Eingabe des Kalkulators | fertig (Vergleichspreise mit Quelle in der Detailansicht; Zuschlag/What-if-Seite) | src/vergleichspreise.py, src/seite_zuschlag.py, src/pages/1_Zuschlag_und_What-if.py | B6a, B6b |
| Meilenstein 1: Parsing und strukturierte Daten | parse(), Datenvertrag | fertig | src/lv_parser.py, docs/data-contracts.md (L21) | – |
| Meilenstein 2: Fehlererkennung und Plausibilität | Nr. 1–4, 15–17 | offen | src/pruefung_widerspruch.py, src/pruefung_formal.py | B1 |
| Meilenstein 3: Risikobewertung und Nachträge | Nr. 5–14, 18 | offen | – | B1, B2 |
| Meilenstein 4: historische Projektdaten (optional) | bepreiste Dateien (B6) und Nachträge (B3, Rückblick-Test) im Datensatz (T2) | offen | docs/decisions.md „B0b: T2“ | B3, B6 |
| Meilenstein 5: What-if (Materialpreise, Alternativen) | Zuschlags-Rechner, What-if nur mit Eingaben des Kalkulators | fertig (nur Eingaben des Kalkulators) | src/seite_zuschlag.py, src/pages/1_Zuschlag_und_What-if.py | B6a |
| Deliverable: Demo Web-App mit Upload und Risikobericht | Streamlit-App, Fundliste, Belegansicht, Bestätigen/Verwerfen, Export .xlsx (seit B1r mit Legende, Menge/EP/GP, Übersicht für den Kalkulator) | fertig | src/app.py, src/bericht.py, src/test_bericht.py; ea262c5, 77467fd, 6c17f70 | B7 (Demo-LV) |
| Goal: Nachtragspotenzial und Streitpunkte (Sicht) | Seite und Blatt „Nachtrag und Streitpunkte“ aus vorhandenen Regel-Funden, keine neuen Funde | fertig auf arbeit/M2 | src/nachtrag_streit.py, docs/bericht_M2.md | M2b |
| Problem: aus früheren Projekten lernen (Entscheidungen) | Erfahrungsdatenbank aus menschlichen Entscheidungen, Anzeige „Erfahrung aus früherer Prüfung, kein Beleg“ | fertig auf arbeit/M2 | src/erfahrung.py, docs/bericht_M2.md | M2c |
| Deliverable: Risikobericht mit KI-Vorschlägen | Blatt „KI-Vorschläge“, getrennt von den Regel-Funden (E13) | fertig auf arbeit/M2 | src/ki_blatt.py, docs/bericht_M2.md | M2, L48 |
| Deliverable: Pitch aus Kalkulator-Sicht | Pitch | offen | – | B8 |

## Prüfungen (input/pruefkatalog.md)

| Punkt | Prüfung/Feature | Status | Beleg (Datei, Test, Commit) | Backlog-ID |
|---|---|---|---|---|
| Nr. 1 | Nennweite (DN) im Kurztext ≠ Langtext | fertig (21 Funde nach B1q; „DN a/b“ als eine Angabe; Bereichsangaben F-Frage; „anderes Bauteil“ L41) | src/pruefung_widerspruch.py; src/test_pruefung.py; src/test_reproduzierbarkeit.py; docs/bericht_B1b.md | B1b |
| Nr. 2 | Betonfestigkeitsklasse im Kurztext ≠ Langtext | fertig (13 Funde) | wie Nr. 1 | B1b |
| Nr. 3 | Menge oder Einheit fehlt | fertig (44 Funde: 38 Auftrags-LV in Stufe 4 nach F1, 6 „Menge 0“; F2 umgesetzt) | src/pruefung_formal.py; src/test_pruefung_formal.py; docs/bericht_B1b.md | B1b |
| Nr. 4 | OZ doppelt im selben LV | fertig (im Datensatz 0 Treffer; Demo-Fall B7) | src/test_pruefung_formal.py (Testdaten); docs/bericht_B1b.md | B1b, B7 |
| Nr. 5 | Bedarfsposition | fertig (162 Funde, gruppiert) | src/pruefung_formal.py; src/test_pruefung_formal.py; docs/bericht_B1b.md | B1b |
| Nr. 6 | Pauschale (psch) | fertig (216 Funde, gruppiert) | src/pruefung_formal.py; src/test_pruefung_formal.py; docs/bericht_B1b.md | B1b |
| Nr. 7 | Produktvorgabe „oder gleichwertig“ | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 8 | Bestand, vorhandene Anlagen | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 9 | Entsorgung, Boden | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 10 | Vorhalten, bauzeitabhängig | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 11 | Vage Formulierung (nur in Kombination) | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 12 | Verweistext („wie vor, jedoch“) | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 13 | Stundenlohnarbeiten | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 14 | Position enthält Bild/Skizze | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| Nr. 15 | Zulage ohne erkennbare Grundposition (früher geplant, L1) | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_struktur.py, src/test_pruefung_struktur.py; Durchlauf 0 FEHLER | B1 |
| Nr. 16 | Gleiche Leistung zweimal im selben Abschnitt (früher „Doppelpositionen“, L1) | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_struktur.py, src/test_pruefung_struktur.py; Durchlauf 0 FEHLER | B1 |
| Nr. 17 | Rechenprüfung Menge × EP ≠ GP | fertig (0 Abweichungen in 1.242 Positionen; Prüfabdeckung „Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“) | src/pruefung_rechnung.py; src/test_pruefung_rechnung.py | B1e |
| Nr. 18 | Ungewöhnliche Mengen | fertig, integriert (B2-Integration 21.11.2026) | src/pruefung_hinweise.py, src/test_pruefung_hinweise.py; Durchlauf 0 FEHLER | B2 |
| früher geplant (L1) | Widersprüche zwischen Positionen | KI-Vorschlag (B5) | test_ki_b5.py | B5 |
| früher geplant (L1) | Tippfehler | KI-Vorschlag (B5) | test_ki_b5.py | B5 |
| früher geplant (L1) | OZ-Lücken | gestrichen (F5, E5) | docs/decisions.md „F5 (E5)“ | – |
| Querschnitt | KI-Gegenprüfung Nr. 1/2 (KI-Vorschlag, entwarnt nie: E13) | offen (Messung Worst Case 9 von 13, L6) | src/ki_pruefung.py, src/ki_client.py, data/qa/ki_messung_lauf1_auswertung_v2.json; 14a762d, B0b | B5 |
| Querschnitt | Doppellauf-Test (E14) | fertig | src/test_reproduzierbarkeit.py (B0b; seit B1b mit Prüfabdeckung) | – |
| Querschnitt | Prüfabdeckung je Datei („prüfbar in N von M Positionen“) | fertig (seit B1p ohne Fußzeilen, Zusammenstellung und umbrochene Kurztexte; Angebot 0 von 274) | src/pruefabdeckung.py, src/test_pruefabdeckung.py; App-Kopf, Übersicht im Risikobericht; B1b | B1b, B1d, B1e |
