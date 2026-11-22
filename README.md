# LV-Prüfassistent – Challenge A (TUM.ai Construction Hackathon)

Der LV-Prüfassistent liest Leistungsverzeichnisse ein und zeigt kalkulierenden Personen, wo sie vor der Angebotsabgabe genauer hinsehen sollten. Jeder Fund steht mit einem wörtlichen Beleg aus dem Original da. **Die Regel findet, das Tool benennt, der Mensch entscheidet.**

## Was das Tool macht

- **Einlesen:** GAEB XML, GAEB 90 und PDF. Excel mit Spalten-Zuordnung ist ohne Beispieldatei der Orga getestet.
- **Prüfen:** 19 Regelprüfungen in vier Stufen, sortiert nach Stufe und Rang.
- **Belegen:** Jeder Fund zeigt OZ, Kategorie, wörtliches Zitat und bei PDFs die Seite.
- **Entscheiden:** Die kalkulierende Person bestätigt, verwirft oder stellt eine Rückfrage. Das Tool setzt keinen Status selbst.
- **Nachtragspotenzial und Streitpunkte:** Eine eigene Sicht ordnet vorhandene Regel-Funde diesen beiden Fragen zu, ohne neue Funde zu erzeugen.
- **Exportieren:** Der Risikobericht (Excel) enthält Übersicht, Funde, Legende, Nachtrag und Streitpunkte sowie KI-Vorschläge. Dazu kommen Bieterfragen als Entwurf.
- **Kalkulation unterstützen:** Vergleichspreise stammen nur aus bepreisten Dateien des Datensatzes und nennen ihre Quelle. Zuschlags-Rechner und What-if rechnen nur mit eigenen Eingaben.
- **Aus früheren Prüfungen lernen:** Gab es in einem anderen LV eine Entscheidung zur gleichen Prüfung mit gleichem Belegtext, zeigt die Detailansicht sie als „Erfahrung aus früherer Prüfung, kein Beleg“.
- **KI nur als Vorschlag:** Die KI läuft nur auf Knopfdruck. Sie ändert weder Priorität, Kategorie, Sortierung noch Filter eines Regel-Funds und kann nie entwarnen.

| Stufe | Bedeutung | Prüfungen |
| --- | --- | --- |
| 1 | Fehlerprüfung | Nr. 1 Nennweite, 2 Betonklasse, 3 Menge oder Einheit fehlt, 4 OZ doppelt, 15 Zulage ohne Grundposition, 16 gleiche Leistung doppelt, 17 Rechenprüfung |
| 2 | Kalkulationsrisiko | Nr. 5 Bedarfsposition, 6 Pauschale, 18 ungewöhnliche Mengen, „Menge 0“ aus Nr. 3 |
| 3 | mögliches Nachtragspotenzial | Nr. 7 Produktvorgabe, 8 Bestand, 9 Entsorgung, 10 Vorhalten, 19 mögliche fehlende Leistung |
| 4 | Unklarheit | Nr. 11 vage Formulierung, 12 Verweistext, 13 Stundenlohn, 14 Bild oder Skizze, Auftrags-LV ohne Menge und Einheit aus Nr. 3 |

## Grundsätze

1. Ein Fund braucht einen wörtlichen Beleg im Original.
2. Das Tool benennt Kategorie und Stufe. Es trifft keine Rechtsaussage.
3. Der Mensch entscheidet. Agenten und KI setzen keinen Status und ändern keine Originaldaten.
4. Die KI schlägt nur vor und darf nie entwarnen.
5. Gleiche Eingabe, gleiches Ergebnis.

## Stand am Datensatz

| Zahl | Aussage | Quelle |
| --- | --- | --- |
| 43 von 44 | Dateien sind lesbar; die übrige ist ein Word-Dokument | `src/test_durchlauf.py` |
| 4.293 | Positionen in den lesbaren Dateien, auch Mehrfachfassungen desselben LV | `docs/bericht_B1p3.md` |
| 1.706 | Funde; das sind Hinweise zur Prüfung, kein Qualitätsmaß | `src/test_durchlauf.py` |
| 1.706 von 1.706 | Funde, deren Belege eine automatische Prüfung ohne Parser wörtlich im Original gefunden hat; das sagt nichts über die fachliche Richtigkeit | `docs/bericht_S3.md`, `src/skeptiker_s2.py` |
| 22 von 22 | Funde der 7 echten Widersprüche im Goldstandard werden gefunden | `data/qa/ki_goldstandard.json` |

Belegprüfung 1.706/1.706 siehe docs/bericht_S3.md; das Ergebnis enthält wörtliche LV-Texte des Datensatzes und ist deshalb nicht im Repo.

Zu Zeitersparnis, Trefferquote oder Vollständigkeit gibt es keine Messung, deshalb nennt dieses Projekt dazu keine Werte.

## Bekannte Grenzen

- Die Funde sind Hinweise zur Prüfung, keine Rechtsberatung und keine Garantie auf Vollständigkeit.
- Spezifikationen und Vorbemerkungen außerhalb von Positionen prüft keine Regel, auch wenn eine Position darauf verweist.
- Nr. 16 kennt nur nummerierte Abschnitte. In `LV_08_Fliesen_und_Natursteinarbeiten.pdf` stehen drei Funde unter verschiedenen Zwischenüberschriften und sind ein möglicher Fehlalarm.
- Zitiert die KI nur die Mengenzeile, wird der Vorschlag verworfen. Mengen-Widersprüche zwischen Positionen findet die KI dadurch teilweise nicht.
- Text in Bildern und Word-Dokumente werden nicht gelesen.
- Der Beleg als Bild der Originalseite (nur PDF, auf Klick) rahmt auf einer Seite den ersten Treffer, nicht zwingend den in der eigenen Position. Bei 337 von 1.118 PDF-Funden steht der Beleg mehrfach auf der Seite; dort kann der Rahmen eine andere Stelle zeigen. Maßgeblich ist der wörtliche Beleg im Text.

## Projektaufbau

Dieses Repo enthält weder die Originaldateien der Challenge noch den KI-Cache. Die Testreihen mit `data/raw` brauchen den Datensatz der Challenge. Ohne `.env` läuft die App mit „KI aus“. Ohne das Ergebnis der Belegprüfung zeigt sie Belege als „noch nicht geprüft“. Bildschirmfotos und zwei interne Protokolle (`docs/pruefprotokoll.md`, `docs/uebergabe_sitzung_B2.md`) sind wegen wörtlicher LV-Texte ebenfalls nicht enthalten; Verweise darauf in der Doku führen deshalb ins Leere.

| Ordner / Datei | Inhalt |
| --- | --- |
| `src/lv_parser.py` | Parser: GAEB XML, GAEB 90, PDF → eine Tabelle |
| `src/validate_parser.py` | Prüft den Parser gegen GAEB-Referenzen + Wiederholbarkeit |
| `src/pruefung_widerspruch.py` | Prüfung Nr. 1/2: Kurz- gegen Langtext (DN, Betonklasse) |
| `src/pruefung_formal.py` | Prüfungen Nr. 3–6, Sortierung, gemeinsamer Einstieg |
| `src/bericht.py` | Risikobericht als Excel-Datei |
| `src/ki_pruefung.py` | KI-Gegenprüfung der Funde Nr. 1/2 (nur auf Knopfdruck), Messung gegen den Goldstandard |
| `src/ki_client.py` | Anbindung Groq (OpenAI-kompatibel) und Anthropic |
| `src/ki_vortest.py` | Vortest und Stabilitätscheck mit erfundenen Positionen |
| `src/etiketten.py` | Etikettenliste für Person B erzeugen und in den Goldstandard übernehmen |
| `src/app.py` | Streamlit-App: Upload, Fundliste, Belege, Entscheidung, Export |
| `src/nachtrag_streit.py` | Sicht und Blatt „Nachtragspotenzial und Streitpunkte“ |
| `src/ki_blatt.py` | Blatt „KI-Vorschläge“ im Risikobericht |
| `src/erfahrung.py` | Erfahrungsdatenbank aus menschlichen Entscheidungen (SQLite) |
| `src/alle_testreihen.py` | Alle Testreihen parallel mit Logdatei je Reihe |
| `data/raw/` | Originaldateien der Challenge (nicht im Repo, `.gitignore`) |
| `data/ki_cache/` | Gespeicherte KI-Antworten; entsteht lokal, nicht im Repo |
| `data/qa/` | Prüfprotokoll-Daten, KI-Goldstandard, KI-Log (Tokens) |
| `input/challenge_A_offiziell.md` | Offizieller Challenge-Text |
| `input/pruefkatalog.md` | Prüfkatalog |
| `docs/` | Leitplanken, Entscheidungen, Datenvertrag, Prüfprotokoll |

## So startest du die App

1. Einmalig `uv` installieren (https://docs.astral.sh/uv/getting-started/installation/).
2. Im Finder im Projektordner `start_app.command` doppelt anklicken. Beim ersten Mal lädt `uv` die festen
   Bibliotheksversionen; danach öffnet sich der Browser mit der Startseite (Entscheidungsübersicht), die erklärt, was das Tool tut.
3. Ein LV hochladen (GAEB XML, GAEB 90, PDF oder Excel). Ohne `.env` mit API-Key läuft die App mit „KI aus“: Alle
   Regel-Funde, Belege, Berichte und Exporte funktionieren, nur die KI-Vorschläge entfallen.
4. Beenden: Ctrl+C im Terminalfenster oder das Fenster schließen.

Die App ist nur auf diesem Rechner erreichbar (localhost) und sendet keine Nutzungsstatistik. Status werden in
`data/findings/` gespeichert. Meldet macOS beim ersten Doppelklick einen unbekannten Entwickler: Rechtsklick auf die
Datei → „Öffnen“.

## Starten

Python 3.12 über `uv` (im System-Python fehlt `pdfplumber`), aus der Projektwurzel:

```bash
uv run --no-project --python 3.12 --with streamlit==1.67.0 --with pdfplumber==0.11.11 --with lxml==6.1.3 --with pandas==3.1.1 --with openpyxl==3.1.5 --with anthropic==2.12.0 --with openai==3.57.0 streamlit run src/app.py --server.address localhost --browser.gatherUsageStats false
```

Tests (ohne API-Kosten):

```bash
uv run --no-project --python 3.12 --with pdfplumber==0.11.11 --with lxml==6.1.3 --with pandas==3.1.1 --with openpyxl==3.1.5 --with anthropic==2.12.0 --with openai==3.57.0 python src/test_ki_pruefung.py data/raw
```

Die übrigen Tests (`src/test_pruefung.py data/raw --stufe2`, `src/test_pruefung_formal.py data/raw`,
`src/test_bericht.py data/raw`) laufen mit demselben Befehl.

## KI-Gegenprüfung

Die App läuft auch ohne KI und zeigt dann „KI aus (kein API-Key)“. Für die KI-Gegenprüfung eine
Datei `.env` in der Projektwurzel anlegen (sie steht in `.gitignore` und wird nie committet):

```text
KI_ANBIETER=groq
KI_MODELL=openai/gpt-oss-120b
GROQ_API_KEY=<eigener Key>
```

Groq (Free Tier) läuft über den OpenAI-kompatiblen Endpunkt `https://api.groq.com/openai/v1`
(Paket `openai`). Limits für dieses Modell laut Groq-Doku: 30 Anfragen/Min., 1.000/Tag,
8.000 Tokens/Min., 200.000 Tokens/Tag; maßgeblich ist der Limits-Tab in der Groq-Console.
Alternativ `KI_ANBIETER=anthropic`, `KI_MODELL=claude-sonnet-5-5` und `ANTHROPIC_API_KEY`.

Die KI wird nur über den Button „KI-Gegenprüfung starten (n Funde)“ aufgerufen, höchstens
50 Aufrufe je Klick, nacheinander. Antworten landen in `data/ki_cache/`; ein zweiter Lauf
macht keinen Aufruf. Die App zeigt Fortschritt, Tokens, Dauer und den Tagesverbrauch.
Über die Kommandozeile für alle lesbaren Dateien:

```bash
uv run --no-project --python 3.12 --with pdfplumber==0.11.11 --with lxml==6.1.3 --with pandas==3.1.1 --with openpyxl==3.1.5 --with anthropic==2.12.0 --with openai==3.57.0 python src/ki_pruefung.py data/raw --ausgabe=data/qa/ki_messung_lauf1.json
```

Der Lauf prüft zusätzlich, getrennt, die 3 „Zusatzfälle, vom DN-Filter bereits aussortiert“
(501-24-01 02.05.0005/0007/0009; nicht in der App) und schreibt die Messtabelle (grob, fein,
je Fund und je Position; strittige Positionen getrennt) in die Ausgabedatei.
