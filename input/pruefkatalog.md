# Prüfkatalog – Entwurf (vom Team zu bestätigen)

Stand: 20.11.2026 abends; synchronisiert mit docs/backlog.md in B0b (21.11.2026); Nr. 1–6 nach E2 in B1b (21.11.2026). Grundlage: Analyse des Challenge-Datensatzes mit
src/lv_parser.py. Status aller Zeilen: **Entwurf**, bis das Team sie bestätigt.

**Kategorien** (wie Regel R6 im BMAD-Prompt): nachweisbarer Fehler /
möglicher Widerspruch / Unklarheit / Risikohinweis.

**Priorität:** 1 = zuerst klären, 4 = nur anzeigen. Seltene, belegbare
Befunde stehen oben, damit die Liste die kalkulierende Person nicht überflutet.

**Treffer** Nr. 1–6: Neuzählung nach B1p (21.11.2026) mit `alle_pruefungen()` über alle 43 lesbaren Dateien in
data/raw (LV-Positionen.docx nicht lesbar), gleiche Zahl im Doppellauf-Test (456 Funde nach B1q; B1b: 464, nach F2: 459, nach B1p: 457). Nr. 7–18: grobe
Stichwortzählung in 2.094 Positionen aus data/parsed/alle_LVs_geparst.xlsx (je LV eine Quelle), nur ein
Anhaltspunkt. Beispiele: Datei, Original-OZ (Seite bei PDF); alle genannten Beispiele vom Skeptiker am
Original geprüft (docs/bericht_B1b.md). **Stand B1p3 (22.11.2026):** 1.706 Funde über alle Prüfungen in 4.293 Positionen; jede Änderung gegenüber 1.688 ist in docs/bericht_B1p3.md je Datei und Prüfung erklärt.

| Nr | Prüfung | Kategorie | Stufe (bisher „Prio“) | Rang in Stufe (bis B1a „Priorität“) | Prüfart | Beleg im Datensatz (Datei, OZ) | Treffer | Handlungsempfehlung (bisher „Empfehlung an die kalkulierende Person“) | Kostenwirkung | Status | Backlog |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Nennweite (DN) im Kurztext ≠ Langtext | möglicher Widerspruch | 1 | 4 | Regel, KI prüft gegen | 8209.003_Leistungsverzeichnis_leer.X83 05.01.4 und 05.01.46; Leistungsverzeichnis.pdf 3.2.60 (S. 30); LV_14b_Dachentwaesserung.pdf .48 (S. 10, Fehlalarm-Verdacht: Futterrohr); Leistungsverzeichnis.pdf 5.3.210 (S. 64, Bereichsangabe „bis DN 250“ / „bis DN 300“, F-Frage) | 21 in 13 Dateien (seit B1q; B1b 24 → B1p 22: 2.1.410 und 4.1.200 waren umbrochene Kurztexte, 5.3.210 kam hinzu → B1q 21: 02.0009 „DN 800/900“ ist eine Angabe) | klärende Rückfrage | direkt: andere Nennweite ändert Material- und Einbaupreis der Position; Höhe ohne Preisbasis nicht bezifferbar (R11) | fertig nach E2 (B1b); Fehlalarme gemeldet (L41) | B1b |
| 2 | Betonfestigkeitsklasse im Kurztext ≠ Langtext | möglicher Widerspruch | 1 | 3 | Regel, KI prüft gegen | LV_00_Roh_und_Erdauarbeiten.pdf 3.1.180 (S. 29); [NUMMER_001]_leer.X83 3.3.4; StBALV23040.D86 03.03.0003; Abgabe LV.pdf 5.3.3 (S. 53); Leistungsverzeichnis_leer.pdf 3.3.3 (S. 25) | 13 in 5 Dateien (4 verschiedene Positionen) | klärende Rückfrage | direkt: andere Betonklasse ändert den Materialpreis der Position | fertig nach E2 (B1b) | B1b |
| 3 | Menge oder Einheit fehlt | nachweisbarer Fehler; „Menge 0“: Risikohinweis; Auftrags-LV ohne Menge und Einheit: Unklarheit | 1 („Menge 0“: 2; Auftrags-LV: 4) | 2 („Menge 0“: 2; Auftrags-LV: 1) | Regel | Auftrags-LV (Austauschphase 86), Menge 0 und Einheit leer: [ORT_024] LV24069.D86 8.1.1, 8.2.1, 8.3.1, 8.5.1, 8.6.8 (Titel 8 „Nachträge“); „Menge 0“: LV_00_Roh_und_Erdauarbeiten.pdf 4.1.120 (S. 63) | 53 in 3 Dateien (B1p3): 38 „Ohne Menge und Einheit (Auftrags-LV)“ (Stufe 4, F1 B1b), 9 „Einheit fehlt“ (LV_13 2.6..1–8, LV_00 1.4.7), 6 „Menge 0“ (LV_00; 5 weitere stehen seit F2 als Feldwert im Nr.-5-Fund); „Menge fehlt“ 0 | klärende Rückfrage („Menge 0“: Befundtext des Teams ohne eigene Empfehlung; Auftrags-LV: vormerken) | direkt: ohne Menge bzw. Einheit geht die Position nicht oder falsch in die Angebotssumme ein; „Menge 0“: nicht in der Angebotssumme, der EP bindet bei Ausführung; Auftrags-LV: Abrechnungsgrundlage offen | fertig nach E2 (B1b), F1/F2 umgesetzt (B1p-Vorlauf) | B1b |
| 4 | OZ doppelt im selben LV | nachweisbarer Fehler | 1 | 1 | Regel | im Datensatz 0 → Demo-Fall in B7; Tests mit selbst gebauten Tabellen | 0 | klärende Rückfrage | direkt: Preise und Abrechnung lassen sich der OZ nicht eindeutig zuordnen | fertig nach E2 (B1b; 0 Treffer, Demo-Fall B7) | B1b, B7 |
| 5 | Bedarfsposition | Risikohinweis | 2 | 3 | Regel | 501-24-01_GAEB-XML_sas.x83 05.01.0001 (<Provis>WithoutTotal</Provis>); LV_21_Natursteinarbeiten.pdf 13.2.10 (S. 1); LV_14_Sanitaeranlage.pdf 1.37 (S. 8); LV_18_Estrich.pdf 11.3.70 (S. 3); LV_17_Trockenbau.pdf 10.1.200 (S. 6) | 162 in 23 Dateien | Risiko einpreisen | bei Abruf: nicht in der Angebotssumme, der EP bindet bei Beauftragung, Menge offen | fertig nach E2 (B1b); App gruppiert | B1b |
| 6 | Pauschale (psch) | Risikohinweis | 2 | 1 | Regel | GAEB-[PROJEKT_004].X83 02.0016 „Wasserhaltung Bach bis 150 l/s“; LV_00_Roh_und_Erdauarbeiten.pdf 1.1.10 (S. 1); 8209.003_Leistungsverzeichnis_leer.D83 01.01.1; [ORT_024] LV24069.D86 01.01.1; Angebot AN24-0305.pdf 1.1.10 (S. 1) | 223 in 28 Dateien (B1p3: +3 LV_04, +4 LV_09, Einheit „pau“) | Risiko einpreisen | direkt: das Mengenrisiko liegt vollständig im Pauschalpreis des Bieters | fertig nach E2 (B1b); App gruppiert | B1b |
| 7 | Produktvorgabe „oder gleichwertig“ | Risikohinweis | 3 | 3 | Regel | 8209.003_Leistungsverzeichnis_leer.X83 (31 Positionen); im Auftrag [ORT_024] LV24069.D86 enthält Nachtrag 1 u. a. „Mehrkosten Armaturen für Ausführung VAG“ | 230 (43 Dateien, alle Formate; Durchlauf B1p3) | vormerken | indirekt: Ein abgelehntes Alternativprodukt kann Mehrkosten beim Material verursachen (Beispiel im Datensatz: [ORT_024] LV24069.D86, Nachtrag 1 „Mehrkosten Armaturen …“); Höhe nicht bezifferbar. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2a |
| 8 | Bestand, vorhandene Anlagen | Risikohinweis | 3 | 4 | Regel (KI offen, B2-L3/L44) | GAEB-[PROJEKT_004].X83 02.0017 „Bestehende Bachverrohrung DN 600 Beton ausbauen, entsorgen“ | 176 (43 Dateien, alle Formate; Durchlauf B1p3) | vormerken | indirekt: unbekannter Zustand des Bestands wirkt auf Aufwand und Entsorgung; Höhe nicht bezifferbar. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2a |
| 9 | Entsorgung, Boden | Risikohinweis | 3 | 1 | Regel (KI offen, B2-L3/L44) | im Auftrag [ORT_024] LV24069.D86: Nachtrag 2 „Zulage Entsorgungskosten …“ | 166 (43 Dateien, alle Formate; Durchlauf B1p3) | vormerken | direkt: Entsorgungskosten hängen von Belastung und Menge ab (Beispiel im Datensatz: [ORT_024] LV24069.D86, Nachtrag 2 „Zulage Entsorgungskosten …“); Höhe nicht bezifferbar. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2a |
| 10 | Vorhalten, bauzeitabhängig | Risikohinweis | 3 | 2 | Regel | [NUMMER_001]_leer.X83 1.2.3 „Bauzaun H 2m vorhalten“, 10.000 mWo; im Auftrag [ORT_024] LV24069.D86: 2× „Zulage … wegen verschobener Bauzeit“ | 181 (43 Dateien, alle Formate; Durchlauf B2-Integration) | vormerken | direkt: Vorhaltekosten steigen mit der Bauzeit (Beispiel im Datensatz: [ORT_024] LV24069.D86, zwei Zulagen „… wegen verschobener Bauzeit“); Höhe nicht bezifferbar. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2a |
| 11 | Vage Formulierung („nach Aufwand“, „ggf.“ …) | Unklarheit | 4 | 4 | Regel (KI offen, B2-L3/L44) | in jeder 4. Position → nur zusammen mit Nr. 5–10 anzeigen | 78 (43 Dateien, alle Formate; Durchlauf B1p3) | nur Hinweis | keine direkte Kostenwirkung: Die Formulierung macht den Umfang unklar; die Kostenwirkung trägt der Risikohinweis an derselben Position. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2b |
| 12 | Verweistext („wie vor, jedoch“) | Unklarheit | 4 | 5 | Regel | LV-Ausdruck-[PROJEKT_004].pdf 02.0015 (S. 10) | 317 (43 Dateien, alle Formate; Durchlauf B2-Integration) | nur Hinweis | keine direkte Kostenwirkung: Der Verweis selbst kostet nichts; Abweichungen zur Bezugsposition können den Preis ändern. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2b |
| 13 | Stundenlohnarbeiten | Risikohinweis | 4 | 3 | Regel | GAEB-[PROJEKT_004].X83 Titel 04 | 43 (43 Dateien, alle Formate; Durchlauf B1p3) | nur Hinweis | indirekt: Der Verrechnungssatz muss Lohn und Zuschläge decken; die Stundenmenge ist meist ein Ansatz. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2b |
| 14 | Position enthält Bild/Skizze | Unklarheit | 4 | 1 | Regel | 501-24-01_GAEB-XML_sas.x83 03.03.0018 | 1 (43 Dateien, alle Formate; Durchlauf B2-Integration) | nur Hinweis | keine direkte Kostenwirkung: Der Inhalt des Bildes ist nicht ausgewertet. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2b |
| 15 | Zulage ohne erkennbare Grundposition | nennt die Zulage eine OZ, die es im LV nicht gibt: nachweisbarer Fehler; findet sich im selben Titel keine passende Grundposition: Unklarheit | 1 | 6 | Regel | laut Vorprüfung 139 Zulagen im Datensatz, keine verweist per OZ, sondern per Bezeichnung (z. B. „Zulage zur Position GGG Rohr DN 300“) [ANNAHME, Zählung Berater 21.11.2026, in B1 nachprüfen] | 3 (43 Dateien, alle Formate; Durchlauf B2-Integration) | Rückfrage stellen | indirekt: Ohne erkennbare Grundposition ist unklar, auf welche Menge und Leistung der Zuschlag kalkuliert wird; Höhe nicht bezifferbar. | umgesetzt, integriert (B2-Integration 21.11.2026) | B1c (Sitzung B2) |
| 16 | Gleiche Leistung zweimal im selben Abschnitt (gleicher Kurztext, Langtext und Einheit, verschiedene OZ, gleicher unterster Titel; Bedarfs- und Wahlpositionen ausgenommen) | möglicher Widerspruch | 1 | 4 | Regel | laut Vorprüfung 84 Gruppen identischer Positionen in 11 Dateien, viele davon in verschiedenen Abschnitten und damit gewollt [ANNAHME, Zählung Berater, in B1 nachprüfen] | 6 (43 Dateien, alle Formate; Durchlauf B1p3; Fehlalarm-Verdacht LV_08, L56) | Rückfrage stellen | direkt möglich: Ist dieselbe Leistung zweimal ausgeschrieben, wird sie zweimal angeboten; ist sie gewollt getrennt, fehlt im Text die Abgrenzung. Höhe = Positionspreis, nicht bezifferbar ohne Preise. | umgesetzt, integriert (B2-Integration 21.11.2026) | B1d (Sitzung B2) |
| 17 | Rechenprüfung Menge × EP ≠ GP (Positionen mit Menge, EP und GP; Toleranz 0,01 € + |Menge| × 0,0005 € aus der Rundung der gedruckten Werte) | nachweisbarer Fehler | 1 | 1 | Regel | im Datensatz 0 Abweichungen; nachgerechnet: Abgabe LV.pdf 248, Angebot AN24-0305.D84 274, Angebot AN24-0305.pdf 274, StBALV23040.D86 249, [ORT_024] LV24069.D86 197 (größte Abweichung 0,0018 €, Angebot 2.3.40); Demo-Fall B7 | 0 (1.242 nachgerechnet) | klärende Rückfrage | direkt: GP weicht vom Produkt ab, Angebotssumme betroffen | fertig nach E2 (B1e) | B1e |
| 18 | Ungewöhnliche Mengen (z. B. Menge 1 bei Einheiten wie m, m², m³; auffällig große Vorhaltemengen; konkrete Regeln erst nach der Datenauswertung) | Risikohinweis | 2 | 4 | Regel | [ANNAHME, Regeln in B2 festlegen] | 32 (43 Dateien, alle Formate; Durchlauf B2-Integration) | Risiko einpreisen | direkt möglich: Weicht die Ausführungsmenge von 1 ab, ändert sich der Positionspreis entsprechend. | umgesetzt, integriert (B2-Integration 21.11.2026) | B2c |
| 19 | Mögliche fehlende Leistung (höchstens 5 Paarregeln auf LV-Ebene: Ortbeton → Schalung, Stahlbeton → Bewehrung, Rohr verlegen → Rohrgraben/Aushub, Aushub → Verfüllen/Abfuhr, Asphalt aufbrechen → wiederherstellen) | Risikohinweis | 3 | 5 | Regel | LV_00_Roh_und_Erdauarbeiten.pdf 2.1.30 (S. 7) | 1 (43 Dateien) | vormerken („prüfen, ob in anderem Gewerk/LV enthalten“) | direkt möglich: Fehlt die Leistung auch in anderen Gewerken, wird sie in der Ausführung zusätzlich nötig; Höhe nicht bezifferbar. | umgesetzt, integriert (B2-Integration 21.11.2026) | B3 |

**Stufe und Rang in Stufe (F1, F2, F4; Team 21.11.2026):** Stufe = Art des Funds nach E3; Anzeige
„1 – Fehlerprüfung“, „2 – Kalkulationsrisiko“, „3 – mögliches Nachtragspotenzial“, „4 – Unklarheit“ (F4).
Rang in Stufe = Rang der Prüfung innerhalb ihrer Stufe (1 = zuerst); E3 im Wortlaut: „selten, sicher,
geldrelevant“ werden gemeinsam abgewogen, keine feste Reihenfolge. Werte vorläufig bestätigt (F1); Nr. 3 wird
nach der Entscheidung zu den 38 Nachtragspositionen neu bewertet (L34). Sortierung in App und Export: Stufe,
Rang in Stufe, OZ. Begründung je Wert (Trefferzahlen: Neuzählung B1b):

| Nr | Stufe | Rang | Prüflogik (sicher, selten) | Wirtschaft (geldrelevant) | Kalkulator [ANNAHME] |
|---|---|---|---|---|---|
| 4 | 1 | 1 | nachweisbarer Fehler, eindeutig im Datenfeld; im Datensatz 0 Fälle | doppelte OZ betrifft Abrechnung und Angebotssumme direkt | wenn es vorkommt, sofort klären |
| 3 | 1 | 2 | nachweisbarer Fehler (Menge oder Einheit fehlt); im Datensatz seit F1 (B1b) 0 Funde in Stufe 1 | Position geht ohne Menge oder Einheit nicht oder falsch in die Angebotssumme ein | Rang wird bei Bedarf neu bewertet (F1 B1a) |
| 2 | 1 | 3 | möglicher Widerspruch, 13 Funde in 4 Positionen | andere Betonklasse ändert den Materialpreis der Position | seltener als Nr. 1, deshalb davor |
| 1 | 1 | 4 | möglicher Widerspruch, 21 Funde; „DN a/b“ seit B1q eine Angabe; Fehlalarme an Anbauteilen (L41) | andere Nennweite ändert Material- und Einbaupreis | wichtig, aber am häufigsten und am wenigsten sicher in Stufe 1 |
| 6 | 2 | 1 | Kennzeichen „psch“ eindeutig, 216 Funde | Mengenrisiko liegt vollständig im Pauschalpreis des Bieters | Pauschalen sind das größere Kalkulationsrisiko |
| 3 („Menge 0“) | 2 | 2 | Feldwert eindeutig, 6 Funde; seltener als Nr. 5 (F2) | nicht in der Angebotssumme, Menge offen (gleiche Wirkung wie Nr. 5) | Bedarfspositionen mit Menge 0 nur noch als Nr.-5-Fund (F2 B1b) |
| 3 (Auftrags-LV) | 4 | 1 | einzige Prüfung in Stufe 4; 38 Funde, alle in einer Auftragsdatei | Abrechnungsgrundlage offen, keine Wirkung auf die Angebotssumme | vormerken (F1 B1b) |
| 5 | 2 | 3 | Vermerk oder Kennzeichen eindeutig, 162 Funde | Bedarfspositionen „ohne GB“ gehen nicht in die Angebotssumme ein | prüfen, ob sie beauftragt werden |

**Kostenwirkung:** Rolle Wirtschaftlichkeit & Kosten, qualitativ (R11, E9: keine Beträge ohne Quelle).
Stufe = bisherige Spalte „Prio“ (B0b.4); „Menge 0“ seit F2 in Stufe 2.

**Prüfabdeckung (B1b):** App-Kopf und Risikobericht zeigen je Prüfung „prüfbar in N von M Positionen“ mit
Grund (src/pruefabdeckung.py). Nr. 1/2 brauchen einen eigenen Langtext, Nr. 3, 5, 6 einen Kurztext.

## Früher geplant, weggefallen (L1, docs/luecken.md)

| Prüfung | Status | Verweis |
|---|---|---|
| Zulage ohne Grundposition | jetzt Nr. 15, geplant | L1, B1 |
| Doppelpositionen | jetzt Nr. 16, geplant | L1, B1 |
| Widersprüche zwischen Positionen | geplant (KI) | L1, B5 |
| Tippfehler | geplant (KI) | L1, B5 |
| OZ-Lücken | gestrichen (F5, Team 21.11.2026; E5-Eintrag in docs/decisions.md) | L1 |

## Bewusst nicht im ersten Prototyp (siehe Scope im BMAD-Prompt)

| Prüfung | Grund |
|---|---|
| Menge × EP ≠ GP | Bepreiste GAEB-Dateien rechnet die Software; Vorabprüfung fand keine Abweichung – aufgehoben (B0a), jetzt Nr. 17 (B1) |
| Preise weichen zwischen zwei Fassungen desselben Angebots ab | Beispiel vorhanden (Abgabe LV.pdf ↔ StBALV23040.D86, OZ 1.1.1 und 1.1.12), aber Preisprüfung ist außerhalb des Scopes |
| Fehlende Leistungen (z. B. Beton ohne Schalung) | Vollständigkeitsprüfung ist außerhalb des Scopes – Ausnahme (Team, 21.11.2026): höchstens 5 Paarregeln als Risikohinweis, B3 |
| Einheit passt nicht zum Text | Braucht Fachregeln. Achtung: „Beton 20 cm“ in m² ist oft korrekt (Abrechnung nach Fläche) |

## Vorschlag für den ersten Durchstich

Nr. 1 und 2 (Kurz- gegen Langtext): Es gibt 19 Kandidaten, davon mehrere von
Hand vorgeprüfte echte Fälle und einen bekannten Fehlalarm als Negativtest.
