# Testfälle und Abnahmekriterien

Stand: 20.11.2026. Alle Zahlen aus Phase 1 (validate_parser.py auf data/raw,
Python 3.12, pdfplumber/lxml/pandas/openpyxl über uv).

## T1 Parser-Basis (darf sich durch keine Änderung verschlechtern)

Aufruf (aus der Projektwurzel):
`uv run --no-project --python 3.12 --with pdfplumber==0.11.11 --with lxml==6.1.3 --with pandas==3.1.1 --with openpyxl==3.1.5 python src/validate_parser.py data/raw`

| Testpaar (PDF / Referenz) | Referenz | gefunden | Menge gleich | Einheit gleich | EP verglichen / gleich | nur im PDF |
|---|---|---|---|---|---|---|
| LV-Ausdruck-[PROJEKT_004].pdf / GAEB-[PROJEKT_004].X83 | 50 | 50 | 50 | 50 | 0 / 0 | 0 |
| Leistungsverzeichnis_leer.pdf / [NUMMER_001]_leer.X83 | 248 | 248 | 248 | 248 | 0 / 0 | 0 |
| Abgabe LV.pdf / StBALV23040.D86 | 249 | 247 | 247 | 247 | 247 / 245 | 1 |
| HEM2301-2_Gesamt-LV.pdf / 8209.003_Leistungsverzeichnis_leer.X83 | 159 | 159 | 159 | 159 | 0 / 0 | 0 |
| Angebot AN24-0305.pdf / Angebot AN24-0305.D84 | 274 | 274 | 274 | 274 | 274 / 274 | 0 |
| Leistungsverzeichnis.pdf / Angebot AN24-0305.D84 | 274 | 274 | 274 | 274 | 0 / 0 | 0 |

Abnahme: Summe gefunden 1.252, Menge und Einheit ohne Abweichung, EP 519 von 521
gleich, keine Zeile "UNTERSCHIED" bei der Wiederholbarkeit (43 Dateien).

Erklärte Abweichungen (kein Parserfehler):
- EP OZ 1.1.1 (PDF 26.000 / D86 16.000) und OZ 1.1.12 (PDF 1.233,33 / D86 6.000):
  stehen so in den Originalen.
- `TE.L0.0009` (D86) = `8.1.3` (PDF), „Muffe PE DN/OD63 SDR11“: anonymisierte OZ (R9).
- `10.01.0001` „Material auf Nachweis zzgl. 18% GK“: Titel 10 „Fremdrechnungen“
  steht nur in StBALV23040.D86/.D84, nicht in [NUMMER_001]_leer.X83 und nicht in
  Abgabe LV.pdf. Unterschied zwischen den Dateien. [BESTÄTIGT, Team und Original]

## T2 Prüfung Nr. 1/2 – Kurztext gegen Langtext (DN, Betonfestigkeitsklasse)

Positiv (muss als "möglicher Widerspruch" mit wörtlichem Beleg gefunden werden):

| Datei | OZ | Seite | Beleg Kurztext | Beleg Langtext |
|---|---|---|---|---|
| 8209.003_Leistungsverzeichnis_leer.X83 | 05.01.4 | – | „Edelstahl-Rohr DN 125“ | „Edelstahlrohr DN 100“, „139,7 x 2,6 mm“ |
| 8209.003_Leistungsverzeichnis_leer.X83 | 05.01.46 | – | „Losflansch DN 125, PN 10“ | „Losflansch, DN 100, PN 10“ |
| [NUMMER_001]_leer.X83 | 3.3.3 | – | „Rückenstütze C20/25“ | „Normalbeton C25/30 (LP) XF2“ |
| LV_00_Roh_und_Erdauarbeiten.pdf | 3.1.180 | 29 | „Stützwand,Stb,C30/37“ | „Beton: C25/30“ |
| Leistungsverzeichnis.pdf | 3.2.60 | 30 | „Muffenschutz aus Gummi DN 300“ | „Muffenschutz aus Gummi DN 500“ |

Fachlicher Hinweis zu 05.01.4: 139,7 mm ist der Außendurchmesser von DN 125,
DN 100 hat 114,3 mm. Quelle: KSB, Druckhöhenverlust-Tabelle
(https://ksb.com/resource/blob/1231434/31092dfc74177a47e38e481aff6dc4ce/dow-druckhoehenverlust3-data.pdf).
Der Fund bleibt "möglicher Widerspruch". [BESTÄTIGT, Team, Chat 20.11.2026]
KSB-Quelle: [OFFEN – nicht belastbar bestätigt] (Team, 21.11.2026, B0b). Belegt ist die Zuordnung
im selben LV: HEM2301-2_Gesamt-LV.pdf ordnet 139,7 mm der DN 125 zu (05.01.10, 05.01.16) und
114,3 mm der DN 100 (05.01.3, 05.01.15). Entscheidung 05.01.4 und 05.01.46: „echter Widerspruch“
(docs/decisions.md, Zeile „B0b: Strittige Positionen …“).

Negativ (darf nicht als Fund erscheinen):
- 501-24-01_GAEB-XML_sas.x83, 02.05.0007, Kurztext „[PERSON_006] DN 2500“:
  DN 110, DN 300, DN 800 im Langtext gehören zu Anbauteilen.
- 501-24-01_GAEB-XML_sas.x83, 02.05.0005, Kurztext „[PERSON_006] rund DN 1200“:
  DN 110 (Rückstauverschluss) und DN 625 (Öffnung der Abdeckplatte,
  Auflagerringe) im Langtext gehören zu Anbauteilen.
- 501-24-01_GAEB-XML_sas.x83, 02.05.0009, Kurztext „[PERSON_006] DN 2500“:
  DN 110 (Rückstauverschluss), DN 300 (Schachtdurchführung), DN 800 und
  DN 450 (Öffnungen der Abdeckplatte, Betonkragen, Auflagerringe) im Langtext
  gehören zu Anbauteilen.

Beleg für 02.05.0005, 02.05.0007 und 02.05.0009: Wortlaut am Original geprüft,
docs/pruefprotokoll.md, Abschnitt S1. Aufnahme von 02.05.0005 und 02.05.0009
als Negativ-Tests [BESTÄTIGT, Team, Chat 20.11.2026].

### Stufe 1: die 5 Testdateien
8209.003_Leistungsverzeichnis_leer.X83, [NUMMER_001]_leer.X83,
Leistungsverzeichnis.pdf, LV_00_Roh_und_Erdauarbeiten.pdf,
501-24-01_GAEB-XML_sas.x83.

Referenz (Prüflauf 20.11.2026, src/heuristik_widerspruch_v0.py):
- ohne Filter 17 Kandidaten, identisch mit dem Blatt „Widerspruch-Kandidaten“
  für diese Dateien;
- mit DN-Filter (Langtext nennt genau einen DN-Wert) 14 Kandidaten: die
  5 Positiv-Tests und 9 ungeprüfte mit Status „offen“ – [NUMMER_001]_leer.X83
  1.1.4, 3.3.4, 5.3.3; Leistungsverzeichnis.pdf 2.1.410, 4.1.200, 5.3.100;
  LV_00_Roh_und_Erdauarbeiten.pdf 2.3.90; 501-24-01_GAEB-XML_sas.x83
  02.03.0023, 03.03.0019. Entfernt: 02.05.0005, 02.05.0007, 02.05.0009.

### Stufe 2: alle LVs mit je einer Quelle (32 Dateien)
DATEIEN-Liste in src/heuristik_widerspruch_v0.py plus LV_*.pdf.
Prüfbar mit `python src/heuristik_widerspruch_v0.py data/raw` (Aufruf mit uv
siehe AGENTS.md): ohne Filter 19 Kandidaten, identisch mit dem Blatt
„Widerspruch-Kandidaten“ [BESTÄTIGT, Prüflauf 20.11.2026]. Mit DN-Filter
bleiben 16 (ohne 02.05.0005, 02.05.0007, 02.05.0009). Ungeprüfte Kandidaten
erscheinen mit Status „offen“.

Die App prüft immer genau ein hochgeladenes LV; dort entstehen keine Dubletten.

PDF-Hinweis: Die Textextraktion fügt Leerzeichen ein (z. B. „C 3 0/37“ im
Rohtext von pdfplumber). Belege werden gegen die Parser-Ausgabe zitiert.

## T3 Platzhalter (R9)
Platzhalter wie `[PERSON_006]`, `[NUMMER_001]`, `TE.L0.0009` erzeugen keinen Fund.

## T4 Demo-Fehler für Prüfung Nr. 3 und 4 [OFFEN]
Menge/Einheit fehlt und OZ doppelt kommen im Datensatz nicht vor
(input/pruefkatalog.md). Für die Demo gezielt in eine Kopie einbauen,
nie in data/raw/. Wer, welche Datei: offen.

## Allgemeine Abnahme
- Jeder Fund hat mindestens einen wörtlich auffindbaren Beleg (R5).
- Jeder Fund trägt genau eine Kategorie aus R6.
- Gleiche Eingabe → gleiche Fund-IDs.
