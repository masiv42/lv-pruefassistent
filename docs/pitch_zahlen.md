# Pitch-Zahlen – nur mit Quelle (R11)

Stand: 22.11.2026, 08:35, Sitzung B4, nach Block S3 (Nachweis: docs/bericht_S3.md). Jede Zahl unten darf im Pitch vorkommen, **genau so** und mit dem genannten Bezug. Eine Zahl, die hier nicht steht, wird nicht genannt. Zeitersparnis- oder Genauigkeitswerte gibt es keine, weil es dazu keine Messung gibt.

Befehl für alle Reihen (aus der Projektwurzel, mit den Versionen aus AGENTS.md): `python src/alle_testreihen.py <log-ordner> --jobs 7`.

## Datensatz und Formate

| Zahl | Aussage (so im Pitch) | Quelle |
|---|---|---|
| 44 | Dateien im Datensatz der Challenge | data/qa/raw_pruefsummen.txt (E11) |
| 43 von 44 | Dateien liest das Tool; die eine nicht lesbare ist ein Word-Dokument (LV-Positionen.docx) | test_durchlauf.py: 43 OK, 1 HINWEIS |
| 3 | Formate: GAEB XML (4 Dateien), GAEB 90 (5 Dateien), PDF (34 Dateien) | test_durchlauf.py, Spalte Format je Datei |
| 4.293 | Positionen in den 43 lesbaren Dateien (GAEB XML 753, GAEB 90 1.128, PDF 2.412; auch Mehrfachfassungen desselben LV) | test_durchlauf.py, Summe „Positionen“ je Datei |
| 64 | Positionen, die der PDF-Parser zunächst nicht erkannt hat und die nach dem Abgleich mit den Mengenzeilen im Original ergänzt wurden | docs/bericht_B1p3.md |
| 2 | reine Preisdateien ohne Texte (die Regelprüfungen auf Text laufen dort nicht, Hinweis in der App) | test_durchlauf.py „(nur Preise)“: StBALV23040.D84, Angebot AN24-0305.D84 |

## Funde je Prüfung (Durchlauf über alle 43 Dateien)

Quelle für alle Zeilen: test_durchlauf.py, Zusammenfassung „Funde je Prüfung“, ohne FEHLER. Alle Prüfungen laufen in App und Export. Die Gesamtzahl ist kein Erfolgswert: Viele Funde sind Hinweise, und Mehrfachfassungen desselben LV zählen mehrfach.

| Nr | Prüfung | Stufe | Funde |
|---|---|---|---|
| 1 | Nennweite (DN) im Kurztext ≠ Langtext | 1 | 21 |
| 2 | Betonfestigkeitsklasse im Kurztext ≠ Langtext | 1 | 13 |
| 3 | Menge oder Einheit fehlt (inkl. Menge 0) | 1, „Menge 0“: 2, Auftrags-LV: 4 | 53 |
| 4 | OZ doppelt im selben LV | 1 | 0 (im Datensatz kein Fall; Demo-LV enthält einen) |
| 5 | Bedarfsposition | 2 | 162 |
| 6 | Pauschale | 2 | 223 |
| 7 | Produktvorgabe „oder gleichwertig“ | 3 | 230 |
| 8 | Bestand, vorhandene Anlagen | 3 | 176 |
| 9 | Entsorgung | 3 | 166 |
| 10 | Vorhalten, bauzeitabhängig | 3 | 181 |
| 11 | Vage Formulierung (nur zusammen mit Nr. 5–10) | 4 | 78 |
| 12 | Verweistext „wie vor, jedoch“ | 4 | 317 |
| 13 | Stundenlohnarbeiten | 4 | 43 |
| 14 | Position enthält Bild/Skizze | 4 | 1 |
| 15 | Zulage ohne erkennbare Grundposition | 1 | 3 |
| 16 | Gleiche Leistung zweimal im selben Abschnitt | 1 | 6 (davon 3 in LV_08 mit Fehlalarm-Verdacht, siehe Grenzen) |
| 17 | Rechenprüfung Menge × EP | 1 | 0 Abweichungen in 1.242 nachgerechneten Positionen (test_pruefung_rechnung.py) |
| 18 | Menge 1 bei Mengeneinheit | 2 | 32 |
| 19 | Mögliche fehlende Leistung (5 Paarregeln) | 3 | 1 |
| | **gesamt** | | **1.706** |

Bieterfragen-Entwürfe aus diesen Funden: **51** (test_durchlauf.py, regelbasiert, je Frage mit wörtlichem Beleg; keine Fragen für Auftrags-LVs).

## Belege am Original

| Zahl | Aussage | Quelle |
|---|---|---|
| 1.706 von 1.706 | Funde, deren Belege eine automatische Prüfung ohne Parser wörtlich im Original gefunden hat | docs/bericht_S3.md (die Ergebnisdatei enthält wörtliche LV-Texte und ist nicht im Repo) |
| 595 von 595 | zuletzt geprüfte Funde (alle Formate), 0 Fehlalarme | src/skeptiker_s2.py --alle, docs/bericht_S3.md |
| 0 | Belege, die der Durchlauf nicht im Positionstext der Parser-Ausgabe findet (R5-Vorcheck, alle 1.706 Funde) | test_durchlauf.py |

So sagen: „Jeder Beleg wurde automatisch wörtlich im Original wiedergefunden.“ Nicht sagen: „Alle Funde sind richtig.“ Die Prüfung belegt die Wörtlichkeit, nicht die fachliche Richtigkeit.

## Gleiche Eingabe, gleiches Ergebnis (E14)

| Zahl | Aussage | Quelle |
|---|---|---|
| 3 Läufe | Alle Prüfungen über alle lesbaren Dateien: drei Läufe byte-gleich, einer in umgekehrter Dateireihenfolge (1.706 Funde) | test_reproduzierbarkeit.py 13/13 |

## Prüfabdeckung (Hinweis, kein Erfolgswert)

| Zahl | Aussage | Quelle |
|---|---|---|
| 0 von 274 | In Angebot AN24-0305.pdf kann Nr. 1/2 keine Position prüfen (kein eigener Langtext im Ausdruck); die App sagt das | test_pruefabdeckung.py, src/pruefabdeckung.py |

## KI

| Zahl | Aussage | Quelle |
|---|---|---|
| 9 von 13 | KI-Gegenprüfung Nr. 1/2: im ungünstigsten Fall 9 von 13 Fällen richtig eingeordnet; deshalb entwarnt die KI nie (E13), sie schlägt nur vor | data/qa/ki_messung_lauf1_auswertung_v2.json; test_auswertung_v2.py |
| 27 von 32 | KI-Prüfungen Tippfehler und Widerspruch: an 32 **erfundenen** Fällen richtig, kein falscher Vorschlag sichtbar, 3 von 8 Widersprüchen verpasst | data/qa/b5_messung.json; docs/bericht_B5.md |

Nicht sagen: „Die KI erkennt x % der Fehler.“ Eine Messung dazu gibt es nicht.

## Rückblick an echten Nachträgen (Messung)

| Zahl | Aussage | Quelle |
|---|---|---|
| 38 | Nachtragspositionen im Auftrags-LV [ORT_024] LV24069.D86 (Nachträge 1–6) | test_rueckblick.py |
| 1 von 7 | Von 7 Nachtragspositionen mit erkennbarem Anlass aus Nr. 7–10 hätte das Tool an 1 Stelle vorab hingewiesen (Entsorgung, 8.2.1 ↔ 03.05.1) | test_rueckblick.py |

Diese Zahl ist eine Messung an **einem** LV, keine Trefferquote. Sie zeigt ehrlich die Grenze von Stichwortregeln.

## Vergleichspreise, Excel, Demo

| Zahl | Aussage | Quelle |
|---|---|---|
| 968 | Positionen mit Preis aus 4 bepreisten Dateien des Datensatzes, als Vergleichspreise mit Quelle (Datei, OZ, EP) | test_vergleichspreise.py |
| 4 | Dateien aus 3 Formaten: Rundreise parse() → Excel → Import ergibt dieselben Positionen (ohne Orga-Beispiel getestet) | test_excel_import.py |
| 19 | Prüfungen Nr. 1–19 mit je einem eingebauten Fall im Demo-LV | test_demo_lv.py |

## Bekannte Grenzen (im Pitch offen nennen)

- **Nr. 16 (Team 01:25, L56):** Die Prüfung kennt nur nummerierte Abschnitte. Die 3 Funde in LV_08 (13.2.6/30, 13.2.7/40, 13.2.8/50) stehen unter verschiedenen Zwischenüberschriften und sind ein möglicher Fehlalarm.
- **Spezifikationen und Vorbemerkungen (L55):** Text außerhalb von Positionen prüft keine Regel, auch wenn eine Position darauf verweist.
- **Beleg als Bild (L61):** nicht Teil der Abgabe. Der Entwurf rahmt nur den ersten Treffer auf der Seite; bei 337 von 1.118 PDF-Funden steht der Beleg mehrfach auf der Seite.
- **KI und Mengenzeile (L49):** Zitiert die KI nur die Mengenzeile, wird der Vorschlag verworfen.

## Nicht verwenden

- Zeitersparnis („x Stunden schneller“): keine Messung.
- Genauigkeit, Trefferquote, Vollständigkeit („findet alle Fehler“): keine Messung; der Rückblick 1 von 7 zeigt das Gegenteil einer Vollständigkeit.
- Geldbeträge aus Funden: Die Kostenwirkung ist je Prüfung beschrieben, aber nicht beziffert (E9).
- Risk Score, Konfidenz-Prozente: gibt es im Tool nicht (R11, E9).
