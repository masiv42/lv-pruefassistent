# Übergabe – Sitzung UI2 (arbeit/ui2)

## FREIGABE NÖTIG

| Nr | Frage | Vorschlag | Folge bei ja | Folge bei nein |
|---|---|---|---|---|
| F1 | P6 (eigene Nachtrag-Ansicht) entfällt, weil M2b sie auf main liefert | ja (Team, erteilt) | Seite 3 bekommt nur Kopf und Design | – |
| F3 | Schreibrecht app.py, Kopf und Design der Seiten 0–3; P0 als B8e | ja (Team, erteilt); bericht.py und test_seite_uebersicht.py bleiben laut F7 Vorschlag an B4 | – | – |
| F4 | Screenshots, Tests und Logs nur mit erfundenen Dateien, Demo-LV nur live | ja (Team, erteilt) | – | – |
| F5 | Auf main 5868994 mit M2/M2b/M2c aufbauen, LV_FINDINGS_DIR und LV_ERFAHRUNG_DB in Temp-Ordnern | erledigt (Team) | – | – |
| F6 | Abnahme im Browser durch die Sitzung mit eingebautem Browser; UI2 startet die App auf 8503 | ja (Team, erteilt) | – | – |
| F9 | „Rückfrage stellen“ neutral statt blau | ja (Team, erteilt: Blau nur Bedienung, Farbe nur nach Kategorie, R6) | umgesetzt in UI2 | – |

## Stand

- **Block:** UI2, Paket 1 = Übernahme aus arbeit/ui (5c43080, F7) + B8e (P0). Basis origin/main 5868994 (Fast-Forward, kein eigener Merge-Commit).
- **Kern-Check:** Punkte 1–6 eingehalten. Keine Prüfregel, keine Fund-ID, keine Sortierung geändert; bericht.py unverändert.
- **Übernommen aus 5c43080 (F7, je Datei mit Test):** src/ui_stil.py + test_ui_stil.py, src/pages/2_Positionen.py + test_ui_positionen.py, .streamlit/config.toml + test_ui_theme.py, Stil-Einbindung in src/pages/0_Uebersicht.py, src/pages/1_Zuschlag_und_What-if.py, src/seite_zuschlag.py (nur Darstellung). Nicht übernommen: .claude/launch.json (Benutzerpfad, Port 8599).
- **src/app.py:** Stand von main vollständig behalten (Seite 3, Kasten „Erfahrung“, Begründungsfeld, KI-Blatt-Filter L59). Stil aus 5c43080 per 3-Wege-Patch nachgetragen; einziger Konflikt (Imports) von Hand gelöst, beide Seiten erhalten. Danach geprüft: `git diff origin/main -- src/app.py` entfernt nur Darstellungszeilen aus 5c43080, keine M2-Funktion.
- **Anpassung an main:** `info.get("tabelle")` statt `info["tabelle"]` in app.py, und die Positionsseite zeigt ihren Hinweis, solange bericht.py den Schlüssel nicht liefert (sonst Absturz auf main).
- **B8e (P0, neu):** src/lv_sitzung.py, src/test_ui_sitzung.py. Ursache des Ablauffehlers belegt (AppTest auf c4ad20f): Streamlit löscht Widget-Zustand beim Seitenwechsel; Upload-Feld, Excel-Zuordnung map_* und Begründungsfeld begr-<fid> verlieren ihren Wert. Jetzt zentral: `lv_aktuell` (Name, Bytes, Zuordnung), `lv_begruendung`; Statusschlüssel lv-<sha> mit Excel-Zuordnung (Auflage 2; ohne Zuordnung unverändert wie bisher); „Anderes LV laden“; X am Upload-Feld entfernt das LV nicht; neuer Upload ersetzt sichtbar („ersetzt …“).

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

## Offen nach Paket 2

- Auflage 8: light-dark() ohne st.context im Browser testen (Sitzung mit eingebautem Browser, App auf 8503).
- Positionen und Übersicht lesen bisher `lv_uebersicht`/`lv_positionen`, die app.py schreibt; nach einem frischen Start ohne Besuch der LV-Prüfung sind sie leer (Hinweis wird gezeigt). Vorschlag: Umstellung auf `lv_aktuell` nach der Integration.
- P5 (Beleg als Bild, nur PDF): freigegeben, wenn UI2 bis 04:45 gepusht ist; Rahmen bis 05:40, mit Test „Zitat nicht gefunden → kein Kasten“ (R5). Was um 05:40 nicht grün ist, kommt mit Stand hierher und wird nicht integriert. Feature-Stopp 06:00 (E8).

## Nächster Schritt

Browser-Abnahme durch das Team auf 8503 (Dark/Light, 1440/1024 px; Ergebnisse als Meldung); P5 bis 05:40; Integration durch B4 mit den Vorschlägen 1 und 2.
