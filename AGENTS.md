<!-- bmad:context -->
<!-- Verified 2026-11-20; kein Git-Repo, daher keine SHA. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## LV-Prüfassistent (TUM.ai Construction Hackathon, Challenge A)

Prototyp, der Leistungsverzeichnisse (GAEB XML, GAEB 90, PDF) einliest und belegbare Prüffunde für kalkulierende Personen zeigt. Python mit pandas, pdfplumber, lxml. Leitplanken in `docs/guardrails.md` (über `CLAUDE.md` geladen), Planung in `docs/`, Prüfkatalog in `input/pruefkatalog.md`.

## Where things are

- Parser und Datenvertrag der LV-Position: `parse()` in `src/lv_parser.py`; Felder in `docs/data-contracts.md`.
- Testfälle und erwartete Zahlen: `docs/acceptance.md`.
- Originaldaten: `data/raw/` (44 Dateien); abgeleitete Ansichten: `data/parsed/`.

## Running and verifying

- Im System-Python fehlt `pdfplumber`; so starten: `uv run --no-project --python 3.12 --with pdfplumber==0.11.11 --with lxml==6.1.3 --with pandas==3.1.1 --with openpyxl==3.1.5 python src/validate_parser.py data/raw`
- Den Parser genauso aufrufen: `uv run … python src/lv_parser.py <datei> --out <ziel>`.
- Referenz-Heuristik für Prüfung Nr. 1/2 aus der Projektwurzel: `uv run … python src/heuristik_widerspruch_v0.py data/raw` (nicht aus `src/` heraus; sie liest `data/raw` relativ).

## Known pitfalls

- GAEB 90: Zu einer Position gehören die Sätze 21–30 (Satz 24, 28, 30 stehen innerhalb von Positionen); `parse()` beendet eine Position seit B1p2 an jedem Satz außer 21–30 (B2-L1 erledigt). Ausschnitte nur aus dem eigenen Block zitieren. (Lehre Sitzung B2)
- Belege aus `parse()` sind nicht immer wörtlich: PDF lässt Zeilen weg (Kopf, „STLB-Bau …“, Punktezeilen), GAEB XML setzt Leerzeichen an `<span>`-Grenzen (B2-L2). Ausschnitte am Original prüfen (PdfSeiten, Gaeb90Bloecke). (Lehre Sitzung B2)
- Team-App (8501) läuft aus dem festen Checkout `../Construction Hackathon main`; nach jedem Merge dort `git checkout --detach main` und neu starten, vorher KI-Cache und Log prüfen (L50). Beim Start `LV_ERFAHRUNG_DB="<Hauptordner>/data/erfahrung/erfahrung.sqlite3"` setzen, sonst bleibt die Erfahrungsdatenbank im Checkout. Vor Demo und Abgabe Status und Datenbank nach archiv/ verschieben (E12 (4)). (Lehre Sitzung B4)
- Commit erst nach geprüftem Exit-Code der Tests, nie Test und Commit in einem verketteten Befehl (FS-B2-8).

- Exporte (Risikobericht, Bieterfragen) nie aus einer App wie Numbers oder Excel nach data/raw speichern; data/raw ist schreibgeschützt (chmod a-w). (Vorschlag Sitzung B2, Team 21.11.2026, FS1)

- `src/lv_parser.py <datei>` ohne `--out` schreibt `<datei>_parsed.xlsx` neben die Eingabe; bei Dateien aus `data/raw/` immer `--out` mit Ziel außerhalb von `data/raw/` setzen.
- Belege aus der Parser-Ausgabe zitieren, nicht aus rohem pdfplumber-Text: der fügt Leerzeichen ein (z. B. „C 3 0/37“ in LV_00, S. 29). Gegengeprüft wird jeder Beleg trotzdem am Original in `data/raw/` (GAEB per Textsuche, PDF über Seitentext oder Seitenbild), nie nur gegen `parse()`.

<!-- /bmad:context -->

## Ergänzungen B0b (außerhalb des bmad-Blocks, Team 21.11.2026)

- Feste Bibliotheksversionen (Python 3.12): `pdfplumber==0.11.11 pandas==3.1.1 lxml==6.1.3 openpyxl==3.1.5 streamlit==1.67.0 openai==3.57.0 anthropic==2.12.0`; nie ohne Teamentscheidung ändern (E14).
- E11-Prüfung: die Prüfsummenliste enthält Dateinamen ohne Pfad, daher im Ordner ausführen: `cd data/raw && shasum -a 256 -c ../qa/raw_pruefsummen.txt`; Anzahl ohne `.DS_Store`: `ls -A data/raw | grep -v -x .DS_Store | wc -l` (44).
- Alle Reihen parallel mit eigener Logdatei und Zusammenfassung (Team 22.11.2026): `python src/alle_testreihen.py <log-ordner> --jobs 7` aus der Wurzel eines sauberen Checkouts, zusätzlich `--with streamlit==1.67.0 --with anthropic==2.12.0 --with openai==3.57.0`.
- Testreihen: `src/test_pruefung.py data/raw --stufe2`, `src/test_pruefung_formal.py data/raw`, `src/test_bericht.py data/raw`, `src/test_ki_client.py`, `src/test_ki_pruefung.py data/raw`, `src/test_status_ablage.py`, `src/test_auswertung_v2.py`, `src/test_pruefstand.py`, `src/test_pruefabdeckung.py data/raw`, `src/test_parser_pdf.py data/raw` (B1p), `src/test_parser_gaeb90.py data/raw` (B1p2), `src/test_regel_dn.py` (B1q), `src/test_ki_b5.py` (B5), `src/test_ki_blatt.py` (M2), `src/test_nachtrag_streit.py data/raw` (M2b, mit `--with streamlit==1.67.0`), `src/test_erfahrung.py` (M2c), `src/test_skeptiker_s2.py data/raw` (L57), `src/test_ui_sitzung.py`, `src/test_ui_start.py`, aus `src/` `test_ui_stil.py`, `test_ui_theme.py`, `test_ui_positionen.py ../data/raw` (Sitzung UI), `src/test_pruefung_rechnung.py data/raw` (B1e), aus `src/` die Reihen von Sitzung B2 (`test_pruefung_hinweise.py`, `test_pruefung_struktur.py`, `test_pruefung_vollstaendigkeit.py`, `test_excel_import.py`, `test_seite_zuschlag.py` mit `--with streamlit==1.67.0`, `test_vergleichspreise.py`, `test_demo_lv.py`, `test_bieterfragen.py`, `test_rueckblick.py`, `test_seite_uebersicht.py`, je mit `../data/raw` wo nötig), Durchlauf-Test `python test_durchlauf.py ../data/raw` aus `src/` (B1t, Sitzung B2; integriert), Doppellauf `src/test_reproduzierbarkeit.py data/raw` (E14), dazu `src/validate_parser.py data/raw` (ergänzt in B1b, F3).
- Browser-Prüfungen durch Agenten nur über den launch.json-Eintrag `lv-app-agent` (Port 8502, `LV_FINDINGS_DIR` in einem Temp-Ordner); nie Status in `data/findings/` des Projekts schreiben (E12 (4), L19).
