# Bericht B1b – Prüfungen Nr. 1–6 auf Standard E2 (L17)

Stand: 21.11.2026, Branch arbeit/B1b. Zahlen: Neuzählung mit `alle_pruefungen()` über alle 43 lesbaren
Dateien in data/raw (LV-Positionen.docx nicht lesbar); dieselben Zahlen im Doppellauf-Test (464 Funde).
Belege: Skeptiker am Original in data/raw (GAEB XML: Textsuche im XML; GAEB 90: Sätze 21/23/25/26 in cp850;
PDF: Seitentext mit derselben Extraktion wie der Parser, aber ohne Filter), nie nur gegen `parse()`.

**Kern-Check:** Punkte 1–5 eingehalten. Abweichung bei Punkt 6 (Rollenkette E1): Scope-Wächter,
Prioritäten-Auditor und die Erwartung des Kalkulators sind vor der Umsetzung nicht schriftlich festgehalten
worden. Sie stehen in Abschnitt 1 dieses Berichts, nachträglich dokumentiert, nicht rückdatiert. Alle übrigen
Rollen liefen in der Reihenfolge E1. Bestätigung des Kern-Checks durch den Prioritäten-Auditor: Abschnitt 7.

## 1. Rollenkette E1 – Auftrag (nachträglich dokumentiert)

- **Scope-Wächter:** Auftrag im Umfang (Backlog B1b, L17; Nachträge des Beraters als Lücken L34–L37).
  Keine neue Prüfung, keine Preisangaben. Stufe 3 heißt „mögliches Nachtragspotenzial“ (R7). Die
  Prüfabdeckung ist ein Hinweis und unterdrückt keinen Fund. Der Nachtrag 1 wird nicht umgesetzt, sondern
  als F-Frage gestellt, wie vom Team vorgegeben.
- **Prioritäten-Auditor (Auftrag):** Reihenfolge F2, F3, F4 → E2 je Prüfung → Nachträge. Stufe 1 vor
  Stufe 2 bleibt (E3). Die Fundzahl darf sich nur durch Teamentscheidungen ändern; F2 ändert nur Stufe und
  Rang.
- **Kalkulator, Erwartung [ANNAHME]:** „Ich will Stufe 1 auf einen Blick sehen und die über 300 Bedarfs-
  und Pauschalpositionen nur als Liste zum Abhaken. Wenn das Tool in einer Datei gar nicht prüfen kann,
  muss es das sagen, sonst halte ich ‚keine Funde‘ für ‚in Ordnung‘.“

## 2. Ergebnis je Prüfung (E2 (a)–(j))

Gemeinsam für alle sechs: (f) App und Export zeigen Kategorie, Stufe („1 – Fehlerprüfung“ …), „Rang in
Stufe“ und Belege; (g) input/pruefkatalog.md und docs/abdeckung.md aktualisiert; (j) Doppellauf 13/13,
464 Funde, drei Läufe byte-gleich (jetzt einschließlich Prüfabdeckung).

### Nr. 1 – Nennweite (DN) im Kurztext ≠ Langtext

- (a) 24 Funde in 15 Dateien, 12 verschiedene Positionen. Beispiele: 8209.003_Leistungsverzeichnis_leer.X83
  05.01.4 und 05.01.46; Leistungsverzeichnis.pdf 3.2.60 (S. 30); LV_14b_Dachentwaesserung.pdf .48 (S. 10);
  GAEB-[PROJEKT_004].X83 02.0009.
- (b) möglicher Widerspruch, Stufe 1, Rang 4, Handlungsempfehlung: klärende Rückfrage.
- (c) src/test_pruefung.py: T2 positiv (5 Fälle), T2 negativ, DN-Filter (zwei DN-Werte → kein Fund),
  Platzhalter (R9), PDF-Belege auf einer Seite.
- (d) Wirtschaft: direkte Kostenwirkung – eine andere Nennweite ändert Material- und Einbaupreis der
  Position; Betrag ohne Preisbasis nicht bezifferbar (R11).
- (e) Skeptiker: alle 12 verschiedenen Positionen (13 Funde, je ein Format) – Belege 13/13 wörtlich im
  Original. Inhaltlich: echt 5.1.4, 5.1.46 (Teamentscheidung B0b), 3.2.60 (Muffenschutz DN 300 / DN 500);
  unklar 5.3.100 (Langtext-Beleg nur „DN 150“); **Fehlalarm-Verdacht 8**: anderes Bauteil 1.1.4
  (vorhandener Anschluss DN 150), 2.3.23 (andere Leitung DN 300), 2.3.90 (Schacht DN 1000 / Anschlüsse),
  3.3.19 (Hydrantenstutzen DN 65), .48 (Futterrohr DN 200); Bereichsangabe 2.1.410 und 4.1.200 („> DN 50“ /
  „bis DN 300“); Doppelangabe 02.0009 („DN 800/900“ wird als DN 800 gelesen). Gemeldet als L41, F5.
- (h) Kalkulator [ANNAHME]: **nützlich** – 24 Funde sind schnell am Beleg zu prüfen, die echten sind
  geldrelevant; die Fehlalarmquote der Stichprobe ist hoch, deshalb Vorschlag an die Prüflogik (F5).

### Nr. 2 – Betonfestigkeitsklasse im Kurztext ≠ Langtext

- (a) 13 Funde in 5 Dateien, 4 verschiedene Positionen. Beispiele: LV_00_Roh_und_Erdauarbeiten.pdf 3.1.180
  (S. 29); [NUMMER_001]_leer.X83 3.3.4; StBALV23040.D86 03.03.0003; Abgabe LV.pdf 5.3.3 (S. 53);
  Leistungsverzeichnis_leer.pdf 3.3.3 (S. 25).
- (b) möglicher Widerspruch, Stufe 1, Rang 3, klärende Rückfrage.
- (c) wie Nr. 1 (T2 positiv 3.1.180, 3.3.3; negativ; Platzhalter).
- (d) Wirtschaft: direkt – andere Betonklasse ändert den Materialpreis der Position.
- (e) Skeptiker: alle 4 Positionen am Original (dazu 3.3.3 in allen 4 Formaten) – Belege wörtlich; 3.1.180
  gleiches Bauteil (Stützwand C30/37 / C25/30); 3.3.3, 3.3.4, 5.3.3 Bordstein-Fundament (Kurztext C20/25,
  Langtext Bettung C25/30), deckt sich mit der Prüfung von Person B (decisions.md B0a). Kein Fehlalarm.
- (h) Kalkulator [ANNAHME]: **nützlich**.

### Nr. 3 – Menge oder Einheit fehlt

- (a) 49 Funde in 3 Dateien: 38 „Einheit fehlt (Menge 0)“, alle in [ORT_024] LV24069.D86 Titel 8
  „Nachträge“ (Stufe 1); 11 „Menge 0“ (LV_00_Roh_und_Erdauarbeiten.pdf 9, LV_13_ELT.pdf 2; Stufe 2 seit F2);
  „Menge fehlt“ 0. Beispiele: [ORT_024] LV24069.D86 8.1.1, 8.6.8; LV_00 3.1.340 (S. 32), 4.1.120 (S. 63);
  LV_13_ELT.pdf 1.3.2.35 (S. 19).
- (b) nachweisbarer Fehler, Stufe 1, Rang 2, klärende Rückfrage; „Menge 0“: Risikohinweis, Stufe 2, Rang 2
  (F2), Befundtext des Teams.
- (c) src/test_pruefung_formal.py: Menge fehlt, Einheit None/"" , Menge 0, Menge 0 + Einheit fehlt, beides
  fehlt; negativ: normale Position, Titel, Position ohne Kurztext (R5); echte Datei 38 Funde.
- (d) Wirtschaft: direkt – ohne Menge oder Einheit geht die Position nicht oder falsch in die
  Angebotssumme ein; „Menge 0“: nicht in der Angebotssumme, der EP bindet bei Ausführung.
- (e) Skeptiker, Kurztext und Feldwert am Original: 8.1.1 und 8.6.8 (Satz 21: Menge `00000000000` = 0,
  Einheit leer; Satz 23 mit EP); LV_00 3.1.340 („0,000 psch … Nur Einh.-Pr.“), 4.1.120 („0,000 m“); LV_13
  1.3.2.35 („0,000 m … Nur Einh.-Pr.“). Alle Belege wörtlich. Befund: 5 der 11 „Menge 0“ sind zugleich
  Bedarfsposition, 3.1.340 erscheint dreimal (L40).
- (h) Kalkulator [ANNAHME]: „Menge 0“ **nützlich** (Stufe 2, gruppiert), Überlappung mit Nr. 5 ist Rauschen
  im Kleinen (F2). Die 38 Nachtragspositionen: **Rauschen in Stufe 1** – siehe Abschnitt 3 (F1).

### Nr. 4 – OZ doppelt im selben LV

- (a) 0 Treffer in 43 Dateien. Demo-Fall in B7.
- (b) nachweisbarer Fehler, Stufe 1, Rang 1, klärende Rückfrage.
- (c) Testtabellen: zwei Schreibweisen derselben OZ, doppelte OZ mit gleichem Kurztext; negativ: keine
  doppelte OZ.
- (d) Wirtschaft: direkt – Preise und Abrechnung lassen sich der OZ nicht eindeutig zuordnen.
- (e) Skeptiker: 0 Funde, keine Stichprobe möglich; so gemeldet.
- (h) Kalkulator [ANNAHME]: **nützlich**, wenn es vorkommt; ohne Treffer kein Rauschen.

### Nr. 5 – Bedarfsposition

- (a) 162 Funde in 23 Dateien. Beispiele: 501-24-01_GAEB-XML_sas.x83 05.01.0001 (<Provis>WithoutTotal</Provis>);
  LV_21_Natursteinarbeiten.pdf 13.2.10 (S. 1); LV_14_Sanitaeranlage.pdf 1.37 (S. 8); LV_18_Estrich.pdf 11.3.70
  (S. 3); LV_17_Trockenbau.pdf 10.1.200 (S. 6).
- (b) Risikohinweis, Stufe 2, Rang 3 (F2), Risiko einpreisen.
- (c) Kennzeichen, PDF-Vermerk, Textvermerk; neu negativ: „Bedarfsgerecht“, „Einheitspreis“ ohne „nur“,
  art_roh ohne Vermerk → kein Fund; echte Datei: 24 <Provis> in 501-24-01.
- (d) Wirtschaft: bei Abruf – nicht in der Angebotssumme, der EP bindet bei Beauftragung, Menge offen.
- (e) Skeptiker: 5 Funde am Original, Belege wörtlich (Vermerk „*** Bedarfsposition ohne GB“ in der Zeile
  der OZ; <Provis> im Item).
- (h) Kalkulator [ANNAHME]: **nützlich, wenn gruppiert** – ungruppiert wäre es Rauschen (L35).

### Nr. 6 – Pauschale (psch)

- (a) 216 Funde in 26 Dateien. Beispiele: GAEB-[PROJEKT_004].X83 02.0016; LV_00_Roh_und_Erdauarbeiten.pdf
  1.1.10 (S. 1); 8209.003_Leistungsverzeichnis_leer.D83 01.01.1; [ORT_024] LV24069.D86 01.01.1; Angebot
  AN24-0305.pdf 1.1.10 (S. 1).
- (b) Risikohinweis, Stufe 2, Rang 1, Risiko einpreisen.
- (c) Einheit „PSCH“ → Feldwert der Original-Einheit; neu negativ: „pauschal“ nur im Text, Einheit m → kein
  Fund; echte Dateien: Anzahl = Positionen mit Einheit psch.
- (d) Wirtschaft: direkt – das Mengenrisiko liegt vollständig im Pauschalpreis des Bieters.
- (e) Skeptiker: 6 Funde am Original, Kurztext und Einheit (X83 `<QU>psch</QU>`, D83/D86 Satz 21 „psch“,
  PDF „1,000 PSCH“ bzw. „1,000 psch“).
- (h) Kalkulator [ANNAHME]: **nützlich, wenn gruppiert** – eine Checkliste der Pauschalen, nicht 216
  einzelne Probleme.

## 3. Nachträge des Beraters

- **Nachtrag 1 (L34):** Am Original bestätigt (Titel 8 „Nachträge“, „Nachtrag 1“; Satz 21 Menge 0, Einheit
  leer; Satz 23 mit EP). Kalkulator [ANNAHME]: In einem Auftrags-LV (Austauschphase 86) sind
  Nachtragspositionen mit Einheitspreis, aber ohne Menge der Normalfall; das ist kein Fehler des LV. Die
  fehlende Einheit muss vor der Abrechnung geklärt werden – ein Hinweis zum Vormerken, kein Fehler.
  Vorschlag als F1 in docs/uebergabe.md; bis zur Entscheidung unverändert.
- **Nachtrag 2 (L35):** 378 von 464 (Nr. 5: 162, Nr. 6: 216) bestätigt. Umgesetzt: Stufe 2 in der App je
  Prüfung aufklappbar gruppiert, mit Anzahl („Nr. 6 Pauschale (psch) · Rang in Stufe 1 · 216 Funde“);
  Stufe 1 offen sichtbar; nichts ausgeblendet; Filter unverändert; Export unverändert vollständig. Kein
  KI-Einfluss (KI nur bei Nr. 1/2, E13).
- **Nachtrag 3 (L36):** Baustein src/pruefabdeckung.py. App-Kopf: Hinweis mit allen eingeschränkten
  Prüfungen und aufklappbare Liste je Prüfung; Export: Zeilen „Prüfabdeckung Nr. n (Name)“ in der
  Übersicht. Angebot AN24-0305.pdf: „prüfbar in 67 von 274 Positionen; übrige 207 ohne eigenen Langtext“.
  Skeptiker: Die 67 sind am Original überwiegend keine Langtexte (umbrochene Kurztexte, Fußzeilen,
  Zusammenstellung) – L38, F3. Die Tests prüfen die 67 nur als Abgleich mit der Zahl des Beraters, nicht als
  Qualitätsaussage.
- **Nachtrag 4 (L37):** Trefferzahlen im Prüfkatalog ersetzt (Abschnitt 2).

## 4. Änderungen durch Teamentscheidungen (F2, F4)

Gegen main (1c030c4) über alle 43 Dateien: Fund-IDs, Belege, Kategorien und Titel unverändert; geändert
`stufe` und `stufe_begruendung` bei 11 Funden („Menge 0“: 3 → 2), `prioritaet_in_stufe` bei 173 Funden
(„Menge 0“ 1 → 2, Nr. 5 2 → 3). Reihenfolge geändert nur in LV_00_Roh_und_Erdauarbeiten.pdf und
LV_13_ELT.pdf. F4: Anzeige-Namen und Spalte „Rang in Stufe“ in App und Export.

## 5. Browser-Prüfung (lv-app-agent, Temp-Ablage)

Auszug aus [ORT_024] LV24069.D86 im Scratchpad (Kopf, Position 01.01.1, Titel 8.1 und 8.2; 9 Positionen,
9 Funde): Hinweis „Prüfabdeckung: Nr. 1 prüfbar in 1 von 9 Positionen; übrige 8 ohne eigenen Langtext …“,
aufklappbare Liste je Prüfung, „Stufe 1 – Fehlerprüfung: 8 Funde“ als offene Tabelle mit Spalte „Rang in
Stufe“, „Stufe 2 – Kalkulationsrisiko: 1 Fund“ mit Gruppe „Nr. 6 Pauschale (psch) · Rang in Stufe 1 · 1 Fund“,
Detail „Stufe 1 (Fehlerprüfung) · Rang in Stufe: 2“, Ablage „Temp-Ablage (Agent)“; keine Konsolen- oder
Serverfehler. Das volle Angebot-PDF (345 KB) lässt sich im Agenten-Browser nicht hochladen (kein
Datei-Upload-Werkzeug); „67 von 274“ ist durch src/test_bericht.py (Export) und src/test_pruefabdeckung.py
belegt.

## 6. Kalkulator-Urteile (E2 (h)) [ANNAHME, simulierte Praxissicht]

| Prüfung / Funktion | Urteil |
|---|---|
| Nr. 1 | nützlich (Fehlalarm-Vorschlag F5) |
| Nr. 2 | nützlich |
| Nr. 3 „Einheit fehlt (Menge 0)“ in Nachträgen | Rauschen in Stufe 1 → F1 |
| Nr. 3 „Menge 0“ | nützlich; Überlappung mit Nr. 5 → F2 |
| Nr. 4 | nützlich, wenn es vorkommt |
| Nr. 5, Nr. 6 | nützlich, weil gruppiert |
| Stufen-Namen, „Rang in Stufe“ | nützlich – „Fehlerprüfung“ neben „möglicher Widerspruch“ widerspricht sich nicht mehr |
| Prüfabdeckung | nützlich – sagt endlich, wo nichts zu finden war; beim Angebot-PDF zu optimistisch (F3) |

## 7. Prioritäten-Auditor – Abnahme

Geprüft: E2 (a)–(j) je Prüfung wie oben; Kern-Check mit der Abweichung bei Punkt 6 bestätigt; Fundzahl 464
unverändert, jede Feldänderung durch F2/F4 erklärt; L17, L33, L35, L36, L37, L42 erledigt; neue Lücken L34,
L38–L41 mit F-Frage; E11 und E12 (4) im Fertig-Check (docs/uebergabe.md). **B1b abgenommen mit Vorbehalt:**
Nr. 3 bleibt bis F1 in der jetzigen Einordnung; die Prüfabdeckung für Angebot AN24-0305.pdf ist bis F3 zu
günstig.
