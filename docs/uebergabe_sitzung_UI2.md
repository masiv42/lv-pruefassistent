# Übergabe – Sitzung UI2 (arbeit/ui2)

## BEREIT ZUR INTEGRATION – arbeit/ui3 @ 2991fb2 (Team-Freigabe nach Browser-Abnahme, 22.11.2026)

- Stand: arbeit/ui3, Commit 2991fb2 (enthält Merge origin/main b3a4c41, 11 Commits, ohne Konflikt).
- Tests auf diesem Stand: alle_testreihen 36/36 grün, Doppellauf 13/13, Durchlauf 0 FEHLER, test_ui3_oberflaeche 104/104,
  test_ui_belegbild 28/28 (data/raw, nur Zählung), Fund-IDs 1.706 mit Hash 2f84ca3348aa94a1 gleich main 51987b4,
  E11 44/44, data/findings unberührt. Bibliotheken unverändert laut AGENTS.md.
- Browser-Abnahmen: 796adee und 0684e6a durch das Team, letzte Punkte (Kontrast Status-Segment, Zuschnitt Belegbild)
  in 2991fb2 behoben; Freigabe „bereit zur Integration“ durch das Team.
- Für B4: Die Prüfseite liegt in src/pages/funde.py (app.py ist die Navigation); src/pages/0_Uebersicht.py ist nicht in
  der Navigation (Lücke-Vorschlag); geänderte fremde Datei src/test_erfahrung.py (nur Dateiname der Prüfseite, gemeldet).
- Offen beim Team: Drehbuch-Vorschlag (docs/demo_drehbuch.md), Eintrag „E8 für Redesign aufgehoben“ in docs/decisions.md,
  Lücke 0_Uebersicht.py, Vorschlag Sprung vom Nachtrag-Fund zur Fundseite (nicht gebaut).

## BLOCK UI3 – Redesign (Branch arbeit/ui3, ab 06:10; vor dem Code)

**Auftrag (Team, Chat 06:0x):** Komplettes Redesign von Oberfläche und Architektur, verständlich für neue Nutzer, nach den
Team-Entwürfen „Entscheidungsübersicht“ und „Projektbriefing / Arbeitswarteschlange / Belegfokus“. E8 für das Redesign
aufgehoben, Streamlit mit eigenem HTML/CSS, React nur bei echtem Mehrwert (nicht genutzt: npm/Build vor 12:00 zu riskant).
arbeit/ui2 (2751b22) bleibt Rückfall und läuft unverändert auf **8503** (fester Checkout); der Redesign-Stand läuft auf **8505**.

**Stand UI3 (laufend aktualisiert)**

| Meilenstein | Commit | Inhalt | Tests |
|---|---|---|---|
| UI3-0 | fe9d4b5 | Rollenkette, Dateiliste, Vorschlag decisions.md | – |
| UI3-1 | 88cc556 | app.py = Navigation (st.navigation), Prüfseite unverändert nach pages/funde.py; Merge main (I1, I2) | 35/36 → test_erfahrung auf neuen Dateinamen (Aussage gleich) 30/30; Doppellauf 13/13, Durchlauf 0 FEHLER, Fund-IDs 1.706 gleich main, E11 44/44 |
| UI3-2 | 9861ca3 | Designsystem src/oberflaeche.py, gemeinsame Auswertung src/lv_daten.py, Startseite mit Erklärung, Entscheidungsübersicht, Berichte & Export, So funktioniert’s | 36/36, test_ui3_oberflaeche 72/72, Doppellauf 13/13, Durchlauf 0 FEHLER, Fund-IDs 1.706 gleich main, E11 44/44 |
| UI3-3 | (dieser Commit) | „Funde prüfen“ neu: Arbeitswarteschlange (Status-, Stufen-, Kategorie-Filter, Suche, Gruppen je Stufe, „Weitere anzeigen“) und Belegfokus; Entscheidung bleibt sichtbar, „Nächster offener Fund“; Logik unverändert | 36/36, test_ui3_oberflaeche 72/72, ui_sitzung 32/32, erfahrung 30/30, ui_belegbild 22/22, Doppellauf 13/13, Durchlauf 0 FEHLER, Fund-IDs 1.706 gleich main |

**UI3-6 – Design neu ausgerichtet (Team 07:1x: „sieht nach KI aus“, /frontend-design, /unslop):**
- Richtung: akribisch, nüchtern, beweisend; Welt = die geprüfte LV-Seite (Papier, OZ am Rand, Textmarker des Prüfers).
- Entfernt: Versal-Labels mit Sperrung, blau getönte Flächen, blaues Logo-Kästchen, gleich große Kachel- und Kartenraster,
  farbige Seitenbalken, Pillen mit Pastellfläche, Gewichte über 600.
- Neu: Graphit statt Navy; Überschriften in ui-serif (New York auf dem Mac, sonst Georgia; keine Downloads), OZ in Monospace;
  Kennzahlen als Protokollzeile mit Haarlinien („Noch zu klären“ zuerst); Fundzeilen wie LV-Zeilen mit OZ-Spalte und
  Kategorie-Punkt mit Text; der Beleg als Ausschnitt einer LV-Seite (Papier, OZ-Kopfzeile, Serifen, Textmarker auf den
  wörtlichen Fachangaben); „LV-Karte“: jede Position ein Strich in OZ-Reihenfolge, Positionen mit Fund in der Farbe der
  Kategorie (echte Daten aus info["tabelle"]); Startseite als geteilter Kopf mit einem gekennzeichneten Beispiel-Beleg aus
  einem erfundenen LV; Schritte und Stufen als Tabellen mit Haarlinien statt Karten; Knöpfe in gebrochenem Weiß.
- Tests: 36/36 Reihen, test_ui3_oberflaeche 73/73, ui_belegbild 22/22, Doppellauf 13/13, Durchlauf 0 FEHLER, Fund-IDs 1.706
  gleich main, E11 44/44. Sichtprüfung im echten Browser weiterhin durch das Team (8505).

**Korrekturauftrag Team (08:3x) – Stand**
- Rollenkette (vor dem Code): Scope nur Darstellung/Kennzeichnung; Auditor A1→A4, dann B, C nur bei Zeit; Kalkulator
  [ANNAHME] „Rot nur für echte Fehler, Beleg-Status sichtbar“; Daten: Positionen je Zeile von info["tabelle"]; Prüflogik:
  keine Regel, neue Tests; Kosten: keine neue Zahl; Skeptiker: Beleg-Status aus derselben S2-Quelle wie der Bericht;
  Oberfläche: Rot nur Kategorie, Grün nur „bestätigt“/„Beleg geprüft“.
- UI3-7 (037bde1): die offenen Änderungen der Sitzung (LV-Blatt, Positionsblatt, Abschnittsmarken) vor Block A committet.
- Block A (8088a1c): A1 Fehlerprüfung neutral mit „davon N nachweisbare Fehler“, Statusleiste neutral, Beispielblatt
  Widersprüche in Bernstein mit Katalogbegriffen; A2 ui.beleg_kennzeichnung/beleg_label_html für Übersicht und Funde;
  A3 ui.positionen_mit_fund für Kopf und LV-Karte; A4 Filter und Belegfokus brechen um (CSS, keine verschachtelten
  Spalten). Testanpassung: Euro-Prüfung der Übersicht auf Text außerhalb der Fundtexte begrenzt (Grund: bepreistes
  Test-LV, Nr. 17 nennt GP laut LV); Aussage „keine vom Tool erzeugten Beträge“ bleibt.
- Block B: B1 kompakter Kopf mit LV („Entscheidungsübersicht“, Datei, Stand, Export), „Zuerst klären“ vor der LV-Karte,
  Kennzahlen kompakter; B2 eine Filterzeile, schmale Kennzeile, Tabelle bis 12 Zeilen; B3 Nachtrag und Zuschlag mit dem
  neutralen Hinweis-Baustein (Wortlaut gleich; einzeln gestartet weiter st.info, damit test_nachtrag_streit gleich bleibt),
  Spaltenbreiten im Nachtrag, Anzeige und Navigation „Mögliches Nachtragspotenzial“ (SEITENTITEL bleibt: Blattname im
  Export, Tests). Testanpassung B1: Leitfrage nur ohne LV.
- Block C: LV-Karte färbt nach dem Fund mit der höchsten Stufe (Text und Logik, Test), Drehung des Beispielblatts entfernt.
  Filter-Chips ruhiger: nicht gemacht.
- **Offen:** Browser-Messung (A4, B1 „erste Fundzeile ohne Scrollen bei 1440 × 900“, B2 „10 Tabellenzeilen“, Dark/Light,
  1024/1440 px) – diese Sitzung hat keinen steuerbaren Browser; App für die Prüfung auf http://127.0.0.1:8505.
- **Vorschlag (nicht gebaut):** Sprung vom Nachtrag-Fund zur Fundseite („Fund öffnen“ je Zeile), wie in den Positionen.

**Geänderte fremde Datei:** src/test_erfahrung.py, nur der Dateiname der Prüfseite (app.py → pages/funde.py); die Aussage
„Erfahrungsdatenbank wird nur aus setze_status der Prüfseite geschrieben“ bleibt.

**Lücke-Vorschlag an das Team (für docs/luecken.md):** src/pages/0_Uebersicht.py ist seit UI3 nicht mehr in der Navigation
(abgelöst durch pages/uebersicht.py). Die Datei und ihr Test (test_seite_uebersicht) bleiben grün; Vorschlag: nach der
Abgabe entfernen oder als Archiv markieren (Team entscheidet, nichts gelöscht).

**Technische Grenze (belegt):** In AppTest läuft nach einem Datei-Upload nur die Seite, nicht app.py. Die Übersicht legt
die gemeinsamen Daten deshalb selbst ab und löst einmal einen Neulauf aus, damit die Seitenleiste sofort das neue LV zeigt.

**Vorschau für Agenten:** LV_UI_VORSCHAU=<Pfad zu erfundener Datei> lädt diese als aktuelles LV (nur Bildschirmprüfung,
Team F4); ohne die Variable ohne Wirkung.

**Rollenkette E1 UI3 – Abschluss**
- **Skeptiker:** (1) Kennzahl „Beleg am Original bestätigt“ hätte bei jeder neu hochgeladenen Datei „0 %“ gezeigt, obwohl
  es dafür keinen Abgleich gibt (S2 kennt nur die Dateien des Datensatzes) → behoben: „–“ mit „für diese Datei kein
  automatischer Abgleich“, Test mit erfundener Datei. (2) Startseite „dauert Sekunden“ = Zeitangabe ohne Quelle → entfernt
  (UI3-4). (3) Hervorhebung im Beleg ändert den Text nicht (Test: ohne <mark> identisch mit dem maskierten Original).
  (4) Kennzahl Fehlerprüfung = Zahl der Stufe-1-Funde, Verteilung je Stufe summiert zur Fundzahl (Test).
- **Kalkulator, Urteil [ANNAHME]:** nützlich – Startseite erklärt in einem Satz, die Übersicht beantwortet „was zuerst“,
  der Belegfokus zeigt Zitat und Begründung nebeneinander; Rauschen-Risiko: lange Listen bei großen LVs, daher Filter
  „Offen“ als Standard und „Weitere anzeigen“.
- **Prioritäten-Auditor:** Meilensteine 1–3 mit grünen Läufen abgenommen; offen: Sichtprüfung im Browser (Dark/Light,
  1440/1024 px, ohne CSS) durch das Team auf 8505, da diese Sitzung keinen Browser hat.

**Abweichung (F7, gemeldet):** src/test_erfahrung.py (Datei von B4) direkt geändert statt nur als Vorschlag – nur der
Dateiname der Prüfseite; nötig, damit die Reihe nach dem Umzug grün bleibt.

**Seiten-Stand:** neu gestaltet: Startseite/Entscheidungsübersicht, Funde prüfen, Berichte & Export, So funktioniert’s.
Nur über den ui_stil-Adapter im neuen Stil (Kopf, Kennzahlen, Belege): Alle Positionen, Nachtrag & Streitpunkte,
Zuschlag & What-if.

**Checkliste Sichtprüfung 8505 (Team):** Dark und Light (Menü ⋮ → Settings) · ganze Fundzeile klickbar, kein zusätzlicher
sichtbarer Knopf unter der Zeile · gewählte Zeile hervorgehoben · Seitenleiste markiert die aktive Seite, Karte „Aktuelles
LV“ direkt nach dem Upload aktuell · 1440 und 1024 px: Kennzahlenleiste und zwei Spalten · Start mit LV_UI_OHNE_CSS=1
bedienbar.

**Vorschlag Demo-Drehbuch (docs/demo_drehbuch.md, Team trägt ein):**
| Zeit | Klick | Zu sehen |
|---|---|---|
| 0:00 | Startseite | Leitfrage „Was muss vor der Angebotsabgabe geklärt werden?“, ein Satz zum Tool, drei Schritte, vier Stufen, Grenzen |
| 0:25 | Demo-LV hochladen | Entscheidungsübersicht: Kennzahlen (Positionen, Fehlerprüfung, Rückfrage-Entwürfe, Belegabgleich), „Zuerst klären“, Belegfokus mit hervorgehobenem DN |
| 1:00 | Zeile „Nennweite (DN) …“ anklicken | Belegfokus rechts: Kurz- und Langtext wörtlich, „Warum relevant“, Bieterfrage (Entwurf) |
| 1:30 | „Fund bearbeiten“ | Seite „Funde prüfen“: Fund geöffnet, KI-Vorschlag getrennt, Entscheidung „Bestätigen“ / „Rückfrage stellen“ |
| 2:10 | „Zur Position“ | Alle Positionen: die OZ mit allen ihren Funden; „Fund öffnen“ zurück |
| 2:40 | Nachtrag & Streitpunkte | Sicht auf Funde Nr. 7–10, 19 |
| 3:10 | Dieselbe Datei erneut hochladen | gleiche Funde, gleiche Reihenfolge, Status bleibt (E14) |
| 3:30 | Berichte & Export | Risikobericht und Bieterfragen (Entwurf) |
Hinweis: „Stufenfarben“ gibt es nicht mehr; Farbe nur nach Kategorie, Stufen neutral.

**Integrationsschluss-Vorschlag:** 10:30 (danach nur Fehlerbehebung), damit B4 vor 12:00 integrieren und prüfen kann.

**Vorschlag für docs/decisions.md (nur das Team trägt ein):** „22.11.2026, 06:0x: E8 für das UI-Redesign aufgehoben (nur
Oberfläche und Navigation, keine Prüflogik); Streamlit + eigenes HTML/CSS, React erlaubt bei echtem Mehrwert; Arbeit auf
arbeit/ui3, arbeit/ui2 bleibt Rückfall. Am Datensatz geprüft: nein (Oberfläche).“

**Rollenkette E1 (vor dem Code)**
- **Scope-Wächter:** Nur Oberfläche, Navigation, Erklärtexte und Zustandshaltung. Keine Prüfregel, keine Fund-ID, keine
  Sortierung, kein neuer Fund. Jede Zahl ist eine Zählung vorhandener Daten (R11), Belege wörtlich und maskiert (R5),
  Begriffe nach R7 und Auftrag Abschnitt 2 (LV, Fund, Beleg; kein „Projekt“, keine „Historie“, kein Score).
- **Prioritäten-Auditor:** Meilensteine mit Push, je alle Reihen grün, Fund-ID-Hash, E11: (1) Gerüst – Router in
  app.py mit st.navigation, Prüfseite unverändert nach pages/funde.py verschoben (kein Design) ~07:00; (2) Start mit
  Erklärung und Entscheidungsübersicht ~08:00; (3) Funde-Seite im neuen Design ~09:15. Integrationsschluss-Vorschlag 10:30.
- **Kalkulator, Erwartung [ANNAHME]:** „Beim Öffnen will ich in einem Satz sehen, was das Tool macht, dann mein LV laden
  und sofort sehen, was ich vor der Abgabe klären muss – mit Beleg daneben, ohne Suchen.“
- **Daten & Parser:** Kennzahlen nur aus vorhandenen Feldern: Positionen (info), Stufe-1-Funde, Funde mit
  Rückfrage-Entwurf (Feld rueckfrage), Anteil „Beleg automatisch am Original bestätigt“ (S2, kein menschlicher Abgleich;
  0 % ist keine Entwarnung, L60), menschliche Entscheidungen (Status). Keine „Rückfrage empfohlen“-Zahl ohne Feld.
- **Prüflogik:** keine Änderung; Tests test_ui_* werden auf die neue Navigation angepasst, Aussagen bleiben.
- **Wirtschaftlichkeit & Kosten:** keine neue Zahl; keine Euro-Beträge außer GP laut LV mit „kein Risikobetrag“.
- **Skeptiker:** Hervorhebung im Beleg (z. B. DN, Betonklasse) nur auf den maskierten wörtlichen Text, Text bleibt gleich;
  KI nie grün, nie in der Liste entwarnend (E13).
- **Oberfläche & Bericht:** Exporte unverändert (gleiche Dateien), nur gebündelt auf „Berichte & Export“.

**Dateien (Ankündigung, Abschnitt C):** neu src/oberflaeche.py, src/lv_daten.py, src/pages/uebersicht.py,
src/pages/funde.py (Inhalt der bisherigen Prüfseite aus app.py, zuerst unverändert verschoben), src/pages/berichte.py,
src/pages/hilfe.py, Tests src/test_ui3_*.py; geändert src/app.py (Router), .streamlit/config.toml, Kopf von
src/pages/1_Zuschlag_und_What-if.py, 2_Positionen.py, 3_Nachtrag_und_Streitpunkte.py, src/test_ui_sitzung.py,
diese Übergabe. src/pages/0_Uebersicht.py bleibt (mit Test), steht aber nicht mehr in der Navigation → Lücke-Vorschlag
an das Team. Hinweis an B4: Änderungen an der Prüfseite stehen nach Meilenstein 1 in src/pages/funde.py statt in app.py.

## BEREIT ZUR INTEGRATION (Stand 05:00, Sitzung UI2 beendet; ab jetzt nur Fehlerbehebung bis 06:00, E8)

| Paket | Commit | Inhalt | Volllauf auf diesem Stand |
|---|---|---|---|
| UI1 | 6886019 | Übernahme aus arbeit/ui (F7), B8e aktuelles LV zentral | Integrationszustand (+ Vorschläge 1, 2): 30/30 grün, Doppellauf 13/13, Durchlauf 0 FEHLER, Fund-IDs 1.706 gleich main |
| **UI2 = Paket 2** | **f22ca0b** (gepusht 04:20) | B8d Startdatei, Seite 3, Erfahrung/Entscheidung, A3, Auflagen 5–7, F9 | 29/30 (rot nur seite_uebersicht bis Vorschlag 2), Doppellauf 13/13, Durchlauf 0 FEHLER, UI-Tests grün, Fund-IDs 1.706 gleich main, E11 44/44 |
| UI3 = P5 | 74b712b | B8b Beleg am Original als Bild (nach Merge main/S2 1ff02ec) | 30/31 (rot nur seite_uebersicht bis Vorschlag 2), Doppellauf 13/13, Durchlauf 0 FEHLER, skeptiker_s2 32/32, UI-Tests grün, Fund-IDs 1.706 gleich main, E11 44/44 |
| UI4 | dieser Commit | Absicherung belegbild (Bildgröße begrenzt), Übergabe | nur belegbild geändert (von app.py importiert): test_ui_belegbild mit data/raw 22/22; voller Lauf von UI3 gilt für alle übrigen Dateien |

Für die Integration nötig: Vorschläge 1 (bericht.py, info["tabelle"]) und 2 (Prüfzeile test_seite_uebersicht.py) unten; Vorschlag 3 (UI-Reihen in alle_testreihen.py/AGENTS.md, F10). Integrationszustand UI3 + Vorschläge 1, 2: test_ui_sitzung 31/31 mit echtem info["tabelle"] (Test-Shim nicht aktiv), test_ui_stil 35/35, test_ui_theme 27/27, test_ui_start 12/12; Volllauf auf sauberem Checkout von 74b712b + Vorschläge 1, 2: **alle_testreihen 31/31 grün** (539 s, Exit 0), Doppellauf 13/13, Durchlauf 0 FEHLER, seite_uebersicht 14/14, skeptiker_s2 32/32; test_ui_positionen mit data/raw 41/41, test_ui_belegbild 19/19 (Stand vor UI4); Fund-IDs 1.706, Hash 2f84ca3348aa94a1 (gleich main).

## FREIGABE NÖTIG

| Nr | Frage | Vorschlag | Folge bei ja | Folge bei nein |
|---|---|---|---|---|
| F1 | P6 (eigene Nachtrag-Ansicht) entfällt, weil M2b sie auf main liefert | ja (Team, erteilt) | Seite 3 bekommt nur Kopf und Design | – |
| F3 | Schreibrecht app.py, Kopf und Design der Seiten 0–3; P0 als B8e | ja (Team, erteilt); bericht.py und test_seite_uebersicht.py bleiben laut F7 Vorschlag an B4 | – | – |
| F4 | Screenshots, Tests und Logs nur mit erfundenen Dateien, Demo-LV nur live | ja (Team, erteilt) | – | – |
| F5 | Auf main 5868994 mit M2/M2b/M2c aufbauen, LV_FINDINGS_DIR und LV_ERFAHRUNG_DB in Temp-Ordnern | erledigt (Team) | – | – |
| F6 | Abnahme im Browser durch die Sitzung mit eingebautem Browser; UI2 startet die App auf 8503 | ja (Team, erteilt) | – | – |
| F9 | „Rückfrage stellen“ neutral statt blau | ja (Team, erteilt: Blau nur Bedienung, Farbe nur nach Kategorie, R6) | umgesetzt in UI2 | – |
| F10 | Vorschlag 3: UI-Testreihen in alle_testreihen.py und AGENTS.md | ja (Team, erteilt: B4 überträgt) | – | – |
| F11 | Datensatz-Teil der UI-Tests (test_ui_belegbild Teil 3, test_ui_positionen data/raw) | ja (Team, erteilt: Teil 3 bleibt als reine Zählung) | – | – |

## Stand

- **Block:** UI2, Pakete UI1 (6886019), UI2 (f22ca0b), UI3 (74b712b), UI4 (Absicherung belegbild, siehe unten). Branch arbeit/ui2, Basis main 5868994, Merge origin/main 1ff02ec (S2).
- **Kern-Check:** Punkte 1–5 eingehalten (keine Prüfregel, keine Fund-ID, keine Sortierung geändert; bericht.py unverändert; kein Status durch Agenten; Fund-IDs 1.706 gleich main). **Abweichung Kern 6:** Die Rollenkette E1 stand nicht vor dem Code, sie ist unten nachgetragen (Abschnitt „Rollenkette E1“); vom Team einmalig akzeptiert.
- **Geänderte Dateien (gegenüber main):** .streamlit/config.toml, README.md (Abschnitt „So startest du die App“), start_app.command, src/app.py, src/ui_stil.py, src/lv_sitzung.py, src/belegbild.py, src/pages/0_Uebersicht.py, src/pages/1_Zuschlag_und_What-if.py, src/pages/2_Positionen.py, src/pages/3_Nachtrag_und_Streitpunkte.py, src/seite_zuschlag.py, src/test_ui_stil.py, src/test_ui_theme.py, src/test_ui_sitzung.py, src/test_ui_start.py, src/test_ui_positionen.py, src/test_ui_belegbild.py, docs/uebergabe_sitzung_UI2.md.
- **Fremde Dateien nur als Vorschlag:** src/bericht.py (Vorschlag 1), src/test_seite_uebersicht.py (Vorschlag 2), src/alle_testreihen.py und AGENTS.md (Vorschlag 3).
- **App für die Abnahme:** http://127.0.0.1:8503 (Status und Erfahrungsdatenbank in Temp-Ordnern).
- **Scratch-Worktrees** (nur für Prüfläufe und den festen ui2-Stand auf 8503, außerhalb des Repos im Scratchpad der Sitzung, in `git worktree list` sichtbar): pruef_5c43080, pruef_main, pruef_ui1, pruef_ui3, demo_ui2. Nicht gelöscht (nichts löschen); entfernen nur auf Wunsch des Teams.

### Paket 1 (UI1) im Detail

- **Übernommen aus 5c43080 (F7, je Datei mit Test):** src/ui_stil.py + test_ui_stil.py, src/pages/2_Positionen.py + test_ui_positionen.py, .streamlit/config.toml + test_ui_theme.py, Stil-Einbindung in src/pages/0_Uebersicht.py, src/pages/1_Zuschlag_und_What-if.py, src/seite_zuschlag.py (nur Darstellung). Nicht übernommen: .claude/launch.json (Benutzerpfad, Port 8599).
- **src/app.py:** Stand von main vollständig behalten (Seite 3, Kasten „Erfahrung“, Begründungsfeld, KI-Blatt-Filter L59). Stil aus 5c43080 per 3-Wege-Patch nachgetragen; einziger Konflikt (Imports) von Hand gelöst, beide Seiten erhalten.
- **Anpassung an main:** `info.get("tabelle")` in app.py; die Positionsseite zeigt ihren Hinweis, solange bericht.py den Schlüssel nicht liefert.
- **B8e (P0):** src/lv_sitzung.py, src/test_ui_sitzung.py. Ursache des Ablauffehlers belegt (AppTest auf c4ad20f): Streamlit löscht Widget-Zustand beim Seitenwechsel. Jetzt zentral: `lv_aktuell` (Name, Bytes, Zuordnung), `lv_begruendung`; Statusschlüssel mit Excel-Zuordnung (ohne Zuordnung wie bisher); „Anderes LV laden“; X am Upload-Feld entfernt das LV nicht; neuer Upload ersetzt sichtbar.

## Rollenkette E1 (nachgetragen, Abweichung Kern 6)

- **Scope-Wächter:** Nur Oberfläche, Startdatei und Zustandshaltung; keine Prüfregel, kein neuer Fund, keine neue Bibliothek; fremde Dateien nur als Vorschlag (F7). Rendern des PDF-Belegs nur aus den Bytes des Originals (A5).
- **Prioritäten-Auditor:** Reihenfolge B8e → B8d → Stil Seite 3/Erfahrung/Entscheidung → A3 → B8b eingehalten; P6 entfallen (F1), P7 durch Downloads im Kopf ersetzt (Konzept), nichts still weggefallen.
- **Kalkulator, Erwartung [ANNAHME]:** „Ich will vom Fund mit einem Klick zum Beleg und zur Position, und die Seite darf mein LV nicht vergessen.“
- **Daten & Parser:** OZ doppelt kommt vor (Demo-LV 0004): wird mit „OZ doppelt, n×“ gezeigt; der letzte Teil der Fund-ID ist nicht immer die OZ (Nr. 16) – Sprünge nutzen deshalb die Positionen des Funds.
- **Prüflogik:** keine Regel geändert; neue Tests test_ui_* (siehe Tests).
- **Wirtschaftlichkeit & Kosten:** keine neue Zahl; Positionswert unverändert mit „kein Risikobetrag“.
- **Skeptiker:** Belegbild am Datensatz: Zitat in 31 PDFs auf der angegebenen Seite gefunden (1.117 von 1.118); nicht gefunden → kein Rahmen, Hinweis. R5-Risiko gefunden und behoben: Übersicht gab Belege als ungeschütztes Markdown aus.
- **Oberfläche & Bericht:** Farbe nur nach Kategorie; Stufen und „Rückfrage stellen“ neutral; KI-Bereich gestrichelt, nie grün; Downloads unverändert (gleiche Dateien, erst beim Klick erzeugt).
- **Kalkulator, Urteil [ANNAHME]:** nützlich (Sprung Fund ↔ Position, Beleg im Original); Rauschen-Risiko: keins neu.
- **Prioritäten-Auditor, Abnahme:** vorbehaltlich der Browser-Abnahme durch das Team und der Integrationsläufe mit den Vorschlägen 1–3.

## Vorschlag 3 (fremde Dateien): UI-Testreihen in die Gesamtläufe

src/alle_testreihen.py, in der ersten Liste (Ordner „.“) ergänzen:

```python
    ("ui_stil", "test_ui_stil.py", []),
    ("ui_theme", "test_ui_theme.py", []),
    ("ui_sitzung", "test_ui_sitzung.py", []),
    ("ui_start", "test_ui_start.py", []),
    ("ui_positionen", "test_ui_positionen.py", ["data/raw"]),
    ("ui_belegbild", "test_ui_belegbild.py", ["data/raw"]),
```

AGENTS.md, Testliste ergänzen: `src/test_ui_stil.py`, `src/test_ui_theme.py`, `src/test_ui_sitzung.py`, `src/test_ui_start.py`, `src/test_ui_positionen.py data/raw`, `src/test_ui_belegbild.py data/raw` (Sitzung UI2, mit `--with streamlit==1.67.0`).

## Diff der Konfliktauflösung src/app.py

```diff
 import ki_b5                                                                    # noqa: E402
-<<<<<<< ours
 import ki_blatt                                                                 # noqa: E402
 import erfahrung                                                                # noqa: E402
-=======
 import ui_stil                                                                  # noqa: E402
->>>>>>> theirs
```

## Vorschläge für fremde Dateien (B4 überträgt, belegt mit Doppellauf)

### 1. src/bericht.py – info["tabelle"] (Auflage 1: enthält Langtext und Seite)

```diff
@@ -138,6 +138,16 @@ def pruefe_lv(pfad, zuordnung=None):
             "einheiten": {r.oz: (r.einheit if isinstance(r.einheit, str) else "") for r in pos.itertuples()}}
+    # Sitzung UI: alle Positionen aus demselben parse()-Lauf wie die Funde (Positions-Explorer)
+    info["tabelle"] = [{"oz": r.oz, "titel": r.titel if isinstance(r.titel, str) else "",
+                        "kurztext": r.kurztext if isinstance(r.kurztext, str) else "",
+                        "langtext": r.langtext if isinstance(r.langtext, str) else "",
+                        "menge": _zahl(r.menge),
+                        "einheit": (r.einheit_roh if isinstance(r.einheit_roh, str) and r.einheit_roh.strip()
+                                    else r.einheit if isinstance(r.einheit, str) else ""),
+                        "ep": _zahl(r.ep), "gp": _zahl(r.gp),
+                        "seite": None if r.seite is None or r.seite != r.seite else int(r.seite)}
+                       for r in pos.itertuples()]
     # B5: Eingaben der KI-Prüfungen (nur auf Knopfdruck in der App; reine Preisdatei ohne Texte: leer)
```

Name: `tabelle` wie im Eintrag „Integration UI“ in docs/decisions.md (im Konzept hieß er `positionen_alle`).

### 2. src/test_seite_uebersicht.py – Prüfzeile Farbschema (Aussage bleibt: eine Farbquelle, Seite und Konfiguration passen zusammen)

```diff
     cfg = tomllib.loads((Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
-    farben = re.findall(r"#[0-9A-Fa-f]{6}", Path(SEITE).read_text(encoding="utf-8").split("FARBEN = ")[1].split("\n")[0])
-    check("Farbschema: nur Akzent und Schrift fest (hell/dunkel folgen dem Browser), Stufenfarben wie in der Seite",
-          set(cfg["theme"]) == {"primaryColor", "font"} and cfg["theme"]["primaryColor"] in farben and len(farben) == 4)
+    check("Farbschema: Dark und Light im Theme, Stufen ohne Warnfarbe (R6)",
+          {"dark", "light"} <= set(cfg["theme"]) and "FARBEN" not in Path(SEITE).read_text(encoding="utf-8"))
```

Begründung: Das neue Theme hat Dark und Light und keine Stufenfarben mehr (Stufen neutral, R6). Ohne diese Zeile ist die Reihe seite_uebersicht auf arbeit/ui2 rot (IndexError beim Suchen von `FARBEN = `).

## Abweichungen 5c43080 (gemeldet, nichts zurückgesetzt)

1. Commit-Nachricht „Update analysis and core functionality“ hat nicht das Format UI<Nr>.
2. .claude/launch.json committet: 8503-Eintrag (soll nie committet werden) und Testserver auf 8599 mit Scratchpad-Pfad, der den Benutzernamen enthält.
3. src/bericht.py (info["tabelle"]) ist committet, laut alter Übergabe noch uncommittet; inhaltlich wie der Eintrag „Integration UI“.
4. Tests auf 5c43080 (abgetrennte Kopie im Scratchpad, data/raw als Link, schreibgeschützt): alle_testreihen 27/27 grün (378 s, Doppellauf 13/13, Durchlauf ohne FEHLER, seite_uebersicht 14/14), test_ui_theme 27/27, test_ui_positionen 41/41 (mit data/raw).

## Tests (Paket 1)

Arbeitsstand vor dem Commit (`python src/alle_testreihen.py <scratchpad> --jobs 7`, Versionen laut AGENTS.md, LV_FINDINGS_DIR/LV_ERFAHRUNG_DB in Temp):
- alle_testreihen: 29/30 grün (695 s parallel), Exit 1. Nicht grün: **seite_uebersicht** (IndexError, erwartet: Prüfzeile in fremder Datei, Vorschlag 2 unten). Doppellauf 13/13, Durchlauf ohne FEHLER, nachtrag_streit 34/34, erfahrung 30/30, ki_blatt 21/21.
- test_ui_stil 35/35, test_ui_theme 27/27, test_ui_sitzung 20/20 (B8e, inkl. Navigation vollständig), test_ui_positionen 40/40 (ohne data/raw; mit data/raw braucht die Reihe info["tabelle"], also Vorschlag 1).
- **Integrationszustand** (sauberer Checkout von UI1 6886019 + Vorschläge 1 und 2 angewandt): alle_testreihen **30/30 grün** (764 s), Exit 0; Doppellauf 13/13, Durchlauf ohne FEHLER, seite_uebersicht 14/14, nachtrag_streit 34/34; test_ui_stil 35/35, test_ui_theme 27/27, test_ui_sitzung 20/20, test_ui_positionen mit data/raw 41/41 (Fund-IDs je LV vollständig); Fund-IDs 1.706, Hash 2f84ca3348aa94a1 (gleich main).

## Datenintegrität

- Fund-IDs über alle Dateien in data/raw (ohne .docx), je ID mit Kategorie, Stufe und Rang: main 5868994 → 1.706 Funde, Hash 2f84ca3348aa94a1; arbeit/ui2 → 1.706 Funde, Hash 2f84ca3348aa94a1 (gleich).
- E11: 44/44 Prüfsummen OK, 44 Dateien ohne .DS_Store; data/raw schreibgeschützt.
- data/findings im Projekt: nicht vorhanden bzw. unberührt; Tests mit LV_FINDINGS_DIR und LV_ERFAHRUNG_DB in Temp-Ordnern.

## Bibliotheken

Unverändert laut AGENTS.md (pdfplumber 0.11.11, pandas 3.1.1, lxml 6.1.3, openpyxl 3.1.5, streamlit 1.67.0, openai 3.57.0, anthropic 2.12.0).

## Paket 2 (UI2, Arbeitsstand nach UI1)

- **P4 B8d:** start_app.command (relativer Start aus dem eigenen Ordner, Versionen wie AGENTS.md, localhost, keine
  Nutzungsstatistik, ohne .env „KI aus“), README-Abschnitt „So startest du die App“ (vor „Starten“; die
  Projektbeschreibung bleibt bei B4). Test src/test_ui_start.py 12/12. Kurzstart headless auf Port 8504 aus einem
  fremden Arbeitsordner: Health „ok“, danach nur dieser Prozess beendet. Der Doppelklick im Finder selbst ist nicht
  automatisiert geprüft (öffnet Terminal und Browser) – Sichtprüfung durch die Browser-Sitzung oder das Team.
- **Seite 3 „Nachtragspotenzial und Streitpunkte“:** Kopf, Navigation, Kennzahlen mit Rahmen; Logik und Texte aus
  src/nachtrag_streit.py unverändert; Seitentest aus test_nachtrag_streit 9/9.
- **Kasten „Erfahrung“** neutral mit Abzeichen „Erfahrung: frühere Entscheidung eines Menschen“; **Begründungsfeld** und
  Statusknöpfe in einem Bereich „Entscheidung“ mit aktuellem Status; Logik von M2c unverändert.
- **Auflage 5:** Test, dass jede Seite in pages/ und app.py in der Navigation steht und `ui_stil.navigation()` aufruft.
- **Auflage 6:** Risikobericht und Bieterfragen als `data=callable` mit Kopie des angezeigten Stands (Status, KI-Cache);
  Test: Funktion liefert .xlsx, Status „bestätigt“ steht im Bericht.
- **Auflage 7:** Diagramm „Funde je Prüfung“ ein neutraler Ton (#7C8BA3), Zahl am Balkenende in deutscher Schreibweise
  und Textfarbe des Themes; Test prüft Ebenen bar + text und keine Farbcodierung.
- **A3:** „Zur Position“ im Fund (LV-Prüfung) und „Fund öffnen“/„Zur Position“ in der Übersicht und auf der
  Positionsseite (st.switch_page, Ziel in lv_fokus, keine URL). Filter (Kategorie, Stufe, Fund-Auswahl; Suche, Titel,
  Stufe, Sortierung, Nur mit Fund, Position) werden je LV gemerkt und überstehen den Seitenwechsel. Ein Sprung macht
  den Ziel-Fund sichtbar (Filter der LV-Prüfung erweitert) bzw. setzt die Filter der Positionsseite zurück, mit
  Hinweis. OZ doppelt: Auswahl zeigt „OZ doppelt, n×“, nie still die erste.
- **R5:** Übersicht „Zuerst ansehen“ zeigt Beleg und Kurztext maskiert (vorher Markdown-Auswertung von LV-Text).
- **F9 (Team: ja):** Status „Rückfrage stellen“ neutral statt blau.
- **Tests Paket 2** (Arbeitsstand vor Commit UI2): alle_testreihen 29/30 (491 s), nicht grün nur seite_uebersicht (Vorschlag 2); Doppellauf 13/13, Durchlauf ohne FEHLER, nachtrag_streit 34/34, erfahrung 30/30; test_ui_stil 35/35, test_ui_theme 27/27, test_ui_sitzung 31/31, test_ui_start 12/12, test_ui_positionen 40/40; Fund-IDs 1.706, Hash 2f84ca3348aa94a1 (gleich main); E11 44/44.
- Test src/test_ui_sitzung.py 31/31. Für die Sprünge simuliert der Test info["tabelle"] im Testprozess nach Vorschlag 1,
  solange bericht.py ihn nicht enthält (mit Hinweiszeile in der Ausgabe); die App ist davon nicht betroffen.

## Paket 3: P5 / B8b Beleg am Original als Bild (UI3)

- Basis: `git merge origin/main` (1ff02ec) nach Prüfung des Diffs: nur S2-Dateien (skeptiker_s2, s2_ergebnis.json, Doku,
  eine neue Reihe in alle_testreihen.py), keine Überschneidung mit UI-Dateien, kein Konflikt.
- Neu: src/belegbild.py, src/test_ui_belegbild.py; app.py: Knopf „Beleg im Original zeigen (Seite n)“ in der
  Detailansicht, nur bei PDF und nur auf Klick. Bild aus den Bytes der hochgeladenen Originaldatei (pdfplumber rendert,
  keine neue Bibliothek), nie aus parse(). Zitatsuche auf der angegebenen Seite unabhängig von Leerraum; Rahmen je
  Trefferzeile in Blau (Auswahl). **Nicht gefunden: kein Rahmen, Hinweis „Zitat auf dieser Seite nicht automatisch
  gefunden – bitte im PDF nachsehen“** (Test: Bild pixelgleich mit der Seite ohne Rahmen, Hinweistext wörtlich).
- Test 19/19 mit erfundener PDF (inkl. App Ende-zu-Ende: Knopf, kein Bild vor dem Klick, Bild nach dem Klick; GAEB ohne
  Knopf). Datensatz (nur Zählung): Zitat in 31 PDFs auf der angegebenen Seite gefunden, 1.117 von 1.118 Funden mit
  Seitenangabe; der eine nicht gefundene zeigt den Hinweis.
- **Tests UI3** (Arbeitsstand nach Merge 1ff02ec): alle_testreihen 30/31 (711 s), nicht grün nur seite_uebersicht
  (Vorschlag 2); Doppellauf 13/13, Durchlauf ohne FEHLER, skeptiker_s2 32/32; test_ui_stil 35/35, test_ui_theme 27/27,
  test_ui_sitzung 31/31, test_ui_start 12/12, test_ui_positionen 40/40, test_ui_belegbild mit data/raw 20/20;
  Fund-IDs 1.706, Hash 2f84ca3348aa94a1 (gleich main); E11 44/44.
- App für die Abnahme: 8503 neu gestartet (Status und Erfahrungsdatenbank in Temp-Ordnern), Health 200. Sie lauscht nur
  auf IPv4: Aufruf **http://127.0.0.1:8503** (über IPv6 [::1] nicht erreichbar; „localhost“ kann je nach Browser
  scheitern, ebenso https://).

## Paket 4 (UI4): Absicherung belegbild

- Automatischer Sicherheitsbefund nach dem Push von UI3 (mittel): Eine PDF mit sehr großem Seitenformat hätte beim Rendern
  ein riesiges Bild erzeugt. Jetzt: längste Bildseite höchstens 2.400 px (Auflösung wird verringert); wäre sie dafür
  unter 12 dpi, erscheint der Hinweis „Seite … ist zu groß …“ statt eines Bilds. Test: Seitenformat 14.400 pt → Bild
  ≤ 2.400 px; 288.000 pt → Hinweis. test_ui_belegbild 21/21.

## Offen nach Paket 2

- Auflage 8: light-dark() ohne st.context im Browser testen (Sitzung mit eingebautem Browser, App auf 8503).
- Positionen und Übersicht lesen bisher `lv_uebersicht`/`lv_positionen`, die app.py schreibt; nach einem frischen Start ohne Besuch der LV-Prüfung sind sie leer (Hinweis wird gezeigt). Vorschlag: Umstellung auf `lv_aktuell` nach der Integration.
- P5: erledigt in UI3 (UI2 um 04:20 gepusht, Freigabe erfüllt). Feature-Stopp 06:00 (E8).

## Nächster Schritt

Browser-Abnahme durch das Team auf 8503 (Dark/Light, 1440/1024 px; Ergebnisse als Meldung); P5 bis 05:40; Integration durch B4 mit den Vorschlägen 1 und 2.
