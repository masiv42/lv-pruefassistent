# Backlog (Leitplanke E4)

Reihenfolge laut Auftrag B0b, B1 geteilt in B1a–B1e (Team, 21.11.2026). Reihenfolge Sitzung B1 (Team, 21.11.2026, 21:20): B1e → B2-Integration → B1p2 → B5 → Debug-Phase; danach Demo, B8. B1c, B1d, B1t, B3 (Rückblick, Bieterfragen, Nr. 19), B4, B6a, B6b, B7-Erzeuger, B8a: von Sitzung B2 gebaut, werden integriert. Gearbeitet wird nur an diesen IDs; Änderungen nur
durch das Team mit Eintrag in docs/decisions.md. Reicht die Zeit nicht, wird am Ende gestrichen (E3),
jede Streichung mit Eintrag in decisions.md (E5). Feature-Stopp: Sonntag, 22.11.2026, 06:00 (E8).

| ID | Inhalt | Stufe | Lücken | Status |
|---|---|---|---|---|
| B0 | Konsolidierung: Abdeckung, Backlog, Lückenprotokoll, Prüfkatalog synchron, Messung v2, Sicherheitskorrekturen L6/L19 (E13), Doppellauf-Test (E14), Bibliotheksversionen, Stand-Bericht | – | L6, L8, L10, L15, L19, L20 | erledigt, abgenommen (c12c88f) |
| B1a | Fundament: Stufe und Priorität in Katalog, Vertrag, App und Export (L30); Prüfstand in App und Bericht (L24); KI-Quelle im Export (L25); kurze Ablage-Anzeige (L32); Doku L21, L23, L27; Test für auswertung_v2 (L29) | – | L21, L23, L24, L25, L27, L29, L30, L32 | erledigt, abgenommen (1c030c4) |
| B1b | Nr. 1–6 auf Standard E2 nachziehen (Stufe, Rang in Stufe, Handlungsempfehlung, Kostenwirkung, Kalkulator-Urteil); F2, F3, F4; Stufe 2 gruppiert; Baustein Prüfabdeckung je Datei | 1–2 | L17, L33–L37 | erledigt, abgenommen (1decf11); Antworten F1–F6 im Vorlauf von B1p umgesetzt |
| B1p | Parser-PDF: Langtext nur aus dem Text der Position (Fuß-/Kopfzeilen, Zusammenstellungs- und Summenzeilen, umbrochene Kurztext-Zeilen nicht im Langtext); nur PDF-Zweig von src/lv_parser.py; Prüfabdeckung neu zählen | – | L38, L45 | erledigt (docs/bericht_B1p.md); Vorlauf F1, F2, F4 (B1b) umgesetzt |
| B1q | Nr. 1 Mehrfach- und Bereichsangaben („DN a/b“, „DN x bis DN y“, „> DN x … bis DN y“); nur an erfundenen Testfällen (E12 (3)); Messung: alle 7 echten Widersprüche des Goldstandards weiter gefunden | 1 | L41 | „DN a/b“ erledigt (docs/bericht_B1q.md); Bereichsangaben: F-Frage F1 in docs/uebergabe.md |
| B1r | Risikobericht für Kalkulatoren lesbar (Stufe als Text, laufende Nr., Menge/Einheit/EP/GP, Übersicht zweigeteilt, Warnzeile bei „-dirty“, KI-Warnhinweis ohne Pfad, Beleg-Status sachlich, Blatt „Legende“) | – | L43 | erledigt (docs/bericht_B1r.md); offen: F2 (Prüfsummen) |
| B1c | Nr. 15 Zulage ohne erkennbare Grundposition | 1 | L1 | von Sitzung B2 gebaut (src/pruefung_struktur.py), integriert (B2-Integration) |
| B1d | Nr. 16 gleiche Leistung im selben Abschnitt | 1 | L1 | von Sitzung B2 gebaut (src/pruefung_struktur.py), integriert (B2-Integration) |
| B1e | Nr. 17 Rechenprüfung Menge × EP; Prüfer-Zuordnung (Formal, Widerspruch, Nachtrag, Klarheit, Mengen, Vollständigkeit, Preis, Tippfehler) in App und Export | 1 | – | erledigt (docs/bericht_B1e.md); Prüfer-Zuordnung vom Team festgelegt (F1, 23:55) |
| B2 | Stufe 3/4, geteilt (Team, 21.11.2026): B2a Nr. 7–10 Nachtragspotenzial, B2b Nr. 11–14 Unklarheiten („vage“ nur in Kombination), B2c Nr. 18 ungewöhnliche Mengen. Sitzung B2 arbeitet parallel im Worktree „Construction Hackathon B2“ auf arbeit/B2, nur mit neuen Dateien (src/pruefung_hinweise.py, src/test_pruefung_hinweise.py, docs/uebergabe_sitzung_B2.md); Integration durch Sitzung B1 nach B1e (Zahlen nach B1p neu zählen) | 2–4 | L44 | integriert (B2-Integration 21.11.2026; Fertig-Check docs/bericht_B2i.md) |
| B3 | fehlende Leistungen (höchstens 5 Paarregeln), Bieterfragen-Export, Rückblick-Test mit den Nachträgen aus [ORT_024] LV24069.D86 – zugleich Teil von Meilenstein 4 (historische Projektdaten = Nachträge im Datensatz, T2) | 2–3 | – | offen |
| B4 | Excel-Import mit Spalten-Zuordnung (ohne Orga-Beispiel getestet, so kennzeichnen) | – | L14 | offen |
| B5 | KI: Tippfehler, Widersprüche zwischen Positionen; L11 (P4-v3 nur mit neuen, erfundenen Testfällen); Ursachenanalyse L6 | 1 | L1, L6, L11 | Tippfehler und Widerspruch zwischen Positionen erledigt als KI-Vorschlag (docs/bericht_B5.md, Prompts B5-T1/B5-W1, Messung 27 von 32 erfundenen Fällen); L11 (P4-v3) und L6 nicht bearbeitet (Zeit, E3) |
| B6 | Vergleichspreise (nur aus bepreisten Dateien des Datensatzes, mit Quelle; T1), Zuschlags-Rechner und What-if (Meilenstein 5), Sortierung nach Geld (L7) – zugleich Meilenstein 4 (historische Projektdaten = bepreiste Dateien, T2) | – | L7, L12 | offen |
| B7 | Demo-LV (nur Kopie, nie data/raw; mindestens ein Fall je Prüfung inkl. Nr. 4); Demo-KI nur aus dem Cache | – | L26 | Demo-LV-Erzeuger integriert, KI-Cache für das Demo-LV gefüllt (B2-Integration) |
| B8 | Feinschliff; sauberes Snapshot-Repo für die Abgabe; Stand-Bericht vereinfachen (F3) | – | L5, L22, L31 | Snapshot lokal bereit, Anlegen nach Freigabe (docs/snapshot_anleitung.md) |

Zuordnung der Lücken L21–L32: F6 (Team, 21.11.2026), siehe docs/luecken.md.
| B1p2 | Parser GAEB 90: Langtext nur aus dem Text der Position (Vorbemerkung des nächsten Bereichs hängt an; 8209.003_Leistungsverzeichnis_leer.D83 Z. 1080–1084; B2-L1); Zeitrahmen 45 min | – | B2-L1 | erledigt (docs/bericht_B1p2.md); PDF-Teil: B1p3 |
| B1p3 | Parser PDF: Positionsgrenze an der Mengenzeile, Unterbeschreibungen bleiben (auch GAEB XML), OZ „1.2..2“, Mengenzeilen ohne Einheit, Einheiten pau/Set; Erwartungswerte aus dem Original, jede geänderte Fundzahl erklärt; Zeitrahmen 105 min | – | FS2, L51–L54 | erledigt (docs/bericht_B1p3.md) |
| L48 | KI-Vorschläge aus B5 im Risikobericht: eigenes Blatt „KI-Vorschläge“ mit Warnhinweis (E13), Quelle und Prompt-Version | – | L48 | erledigt, auf main (docs/bericht_M2.md) |
| M2b | Sicht „Nachtragspotenzial und Streitpunkte“: Seite und Blatt, keine neuen Funde (Team 01:25) | – | L58 | erledigt, auf main (docs/bericht_M2.md) |
| S3 | Belegprüfung aller übrigen Funde in GAEB XML, GAEB 90 und PDF (Team, L60) | – | L60 | erledigt, auf main (docs/bericht_S3.md) |
| S2 | Belegprüfung der 31 Funde aus B1p3 am Original, src/skeptiker_s2.py (Team, F2) | – | L57 | erledigt, auf main (docs/bericht_S2.md) |
| M2c | Erfahrungsdatenbank aus menschlichen Entscheidungen, SQLite (Team 01:25) | – | – | erledigt, auf main (docs/bericht_M2.md) |
| B8b | Beleg am Original als Bild (src/belegbild.py), in der Detailansicht nur auf Klick | – | L61 | nicht integriert (Team 08:26), bleibt auf arbeit/I3 |
| B8c | Positions-Explorer (src/pages/2_Positionen.py) | – | – | erledigt, auf main (docs/bericht_I1.md) |
| B8d | Startdatei start_app.command, Abschnitt „So startest du die App“ in README.md (Projektbeschreibung in README bleibt bei Sitzung B4) | – | – | erledigt, auf main (I2) |
