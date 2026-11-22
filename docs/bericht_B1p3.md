# Bericht B1p3 – PDF-Positionsgrenze, Unterbeschreibungen, fehlende Positionen

Stand: 22.11.2026, Branch arbeit/B1p3. Rollenkette vor dem Code: docs/uebergabe.md.

**Kern-Check:** Punkte 1–6 eingehalten. Keine Prüfregel wurde verändert, kein Status gesetzt, data/raw unberührt.

## Kriterium: Was hinter der Mengenzeile zur Position gehört (F1, 00:20)

Maßgeblich ist die **letzte** Mengenzeile eines Blocks. Danach gilt:

1. Eine **Unterbeschreibung** beginnt mit der Zeile „Unterbeschreibung N:“ und gehört zur Position.
2. Sie endet an „Gemäß … N:“, „Leitbeschreibung:“, „*** …“, an der nächsten OZ oder am Schlussteil. „Unterbeschreibung 2:“ beendet sie nicht.
3. **Aller andere Text** hinter der Mengenzeile ist fremd: Hinweistexte, Spezifikationen, Vorbemerkungen, Abschnittstitel, „zzgl. MwSt.“.
4. Die Zeile „Unterbeschreibung N:“ selbst steht nicht im Langtext, weil das GAEB-Original dort nur eine Nummer führt (`SubDNo`).

GAEB XML liest `SubDescr` (Kurz- und Langtext) zusätzlich in den Langtext. GAEB 90 führt die Texte schon in Satz 25/26.

**Getestet mit Erwartungswerten aus dem Original** (src/test_parser_pdf.py, 65/65):

| Fall | Stellen |
|---|---|
| Unterbeschreibung bleibt | alle 13 Positionen (16 Texte) in Abgabe LV.pdf und Leistungsverzeichnis_leer.pdf gegen den rohen `SubDescr`-Text im X83; einzeln 7.1.5, 7.1.6, 9.1.5 |
| Fremder Text endet | je 4 Positionen in Abgabe LV.pdf und Leistungsverzeichnis_leer.pdf (3.1.8, 3.2.3, 7.1.1, 7.1.4); HEM 06.01.4 (S. 116), 06.01.6 (S. 117); LV-Ausdruck 04.0003 (S. 20); Leistungsverzeichnis 5.3.200; LV_00 2.2.75 |

Beim Textvergleich bleibt das Wort direkt neben einem Platzhalter außen vor, weil die Anonymisierung dort je Format verschieden ersetzt hat (X83 „[PERSON_044], max.“, PDF „[PERSON_044] max.“; R9).

## Positionen: 4.229 → 4.293 (+64)

OZ, Menge, Einheit, EP und GP aller bestehenden Positionen sind unverändert.

| Datei | Positionen | Ursache am Original |
|---|---|---|
| LV_13_ELT.pdf | 138 → 191 | OZ „1.2..2“: 56 Positionen neu, die Sammelblöcke 1.2, 2.1, 2.7 entfallen. 191 = alle Mengenzeilen im Original. Die Teamzahl 183 enthielt 8 Mengenzeilen ohne Einheit nicht (2.6..1–8, S. 49/50) |
| LV_09_Porenbetondach.pdf | 11 → 15 | Einheit „pau“ (9.2.0–3) |
| LV_04_Porenbetonfassade.pdf | 17 → 20 | Einheit „pau“ (9.1.10–30) |
| LV_14a_Betonkernaktivierung.pdf | 34 → 36 | Einheit „Set“ (.14, .25) |
| LV_00_Roh_und_Erdauarbeiten.pdf | 268 → 269 | Mengenzeile ohne Einheit (1.4.7) |
| LV_21_Natursteinarbeiten.pdf | 30 → 31 | 13.4.210: Menge 0,000, ohne Text und Einheit; kein Fund, weil es keinen wörtlichen Beleg gibt (R5) |

Die Schreibweise „a.b..c“ kommt nur in LV_13 vor. Zwei weitere Abweichungen zwischen Mengenzeilen und Positionen sind keine fehlenden Positionen: LV-Schachtbauwerk S. 1 beginnt mitten im LV („20,000 m²“ vor der ersten OZ), und LV_14 8.8 enthält „0,365 m.“ als Zahl im Text.

Langtexte: 167 PDF-Positionen in 13 Dateien sind um fremden Text gekürzt; 13 Positionen im X83 tragen jetzt ihre Unterbeschreibung.

## Funde: 1.688 → 1.706 (+30, −12)

| Datei | neu | entfallen | Erklärung |
|---|---|---|---|
| LV_13_ELT.pdf | Nr. 3 ×8, Nr. 7 ×10, Nr. 8 ×1 | Nr. 7 (1.2), Nr. 8 (2.1), Nr. 11 (1.3.2.12) | Neu: die wieder vorhandenen Positionen, 2.6..1–8 ohne Einheit. Entfallen: Sammelposition 1.2 (Beleg steht jetzt bei 1.2..6), Vorbemerkung des Titels 2.1, Vorbemerkung hinter 1.3.2.12 |
| LV_09 | Nr. 6 ×4, Nr. 10 ×1 | – | neue Pauschalen 9.2.0–3 |
| LV_04 | Nr. 6 ×3 | – | neue Pauschalen 9.1.10–30 |
| LV_00 | Nr. 3 (1.4.7), Nr. 16 (3.1.280/330) | Nr. 13 (3.4.89.0) | Nr. 16: Abschnittstitel hinter 3.1.330 machte die Texte bisher ungleich. Nr. 13: Beleg war die Vorbemerkung des nächsten Abschnitts |
| LV_08 | Nr. 16 (13.2.8/50) | – | wie oben; **Fehlalarm-Verdacht**, L56 |
| HEM2301-2_Gesamt-LV.pdf | – | Nr. 7 (6.1.6, 6.4.4), Nr. 8 (6.1.4, 6.2.1) | Belege aus Spezifikationen hinter der Mengenzeile. 7\|6.4.1 bleibt, ein Beleg weniger (S. 128) |
| Abgabe LV.pdf, Leistungsverzeichnis_leer.pdf | – | je Nr. 9 (3.1.8) | „Abfallentsorgung …“ hinter der Mengenzeile (S. 18/19) |
| LV-Ausdruck | – | Nr. 10 (4.3) | Vorbemerkung Geräte und Fahrzeuge (S. 20) |
| Leistungsverzeichnis.pdf | – | Nr. 13 (7.1.80) | Hinweistext der Folgepositionen (S. 67) |

Je Prüfung: Nr. 3 44→53, Nr. 6 216→223, Nr. 7 223→230, Nr. 8 178→176, Nr. 9 168→166, Nr. 11 79→78, Nr. 13 45→43, Nr. 16 4→6; alle übrigen unverändert.

## Skeptiker am Original (ohne parse())

- **Entfallen (12):** 10 Belege stehen im Seitentext hinter der Mengenzeile, 2 hingen an Sammelpositionen.
- **Neu (30):** Jeder Textbeleg steht wörtlich auf der Seite der Position oder der Folgeseite.
- **Fehlalarm gemeldet (L56):** LV_08 13.2.8/50 liegen unter verschiedenen Zwischenüberschriften ohne OZ; dasselbe gilt für die älteren Paare 13.2.6/30 und 13.2.7/40. Die Regel Nr. 16 blieb unverändert.
- Die 30 neuen Funde und 7|HEM|6.4.1 zeigen in der App „Beleg noch nicht am Original geprüft“, weil data/qa/s2_ergebnis.json nicht von Hand geändert wird.

## Prüfung

- Alle 27 Reihen grün auf cf8a8ae, Doppellauf 13/13 (sechs FS2-Abweichungen ausgetragen), Durchlauf 43 OK, 1 Hinweis, 0 Fehler. Danach nur ein Test ergänzt (test_parser_pdf 65/65) und Doku; kein Code.
- Goldstandard 22 von 22. E11 44/44, data/findings leer.
- Browser (lv-app-agent, Auszüge LV_13 S. 48–50 und Abgabe LV S. 67/68): 2.6..1 mit „Einheit: (leer)“ in Stufe 1, 7.1.5/7.1.6 ohne Fehler, keine Serverfehler.

## Grenzen

- **L55:** Spezifikationen und Vorbemerkungen außerhalb von Positionen prüft keine Regel mehr, auch wenn eine Position darauf verweist („gemäß Spezifikation …“).
- **L56:** Nr. 16 kennt keine Zwischenüberschriften ohne OZ.
- **L49:** KI-Zitat aus der Mengenzeile bleibt verworfen (F3, 23:55).

## Angenommen vorbehaltlich Team (00:45, Punkt 3)

- Einheiten „pau“ (als psch) und „Set“ behoben (L53).
- Mengenzeilen ohne Einheit gelten in allen PDFs, also auch für LV_00 1.4.7 und LV_21 13.4.210 (L54).
- Nr. 16 bleibt bis zu einer Teamentscheidung unverändert (L56).

## Kalkulator-Urteil [ANNAHME]

**Nützlich.** Fehlende Positionen sind das Schlimmste, was ein Prüftool haben kann; „Einheit fehlt“ an 2.6..1–8 würde ich sofort klären. Dass Vorbemerkungen nicht mehr als Beleg der falschen Position erscheinen, macht die Funde glaubwürdiger. **Rauschen-Risiko:** Nr. 16 in LV_08, weil dort verschiedene Bereiche gemeint sein können.

## Prioritäten-Auditor

Abgenommen: Erwartungswerte aus dem Original, jede Positions- und Fundänderung erklärt, Goldstandard 22/22, Doppellauf und Durchlauf grün, Zeitrahmen 105 min eingehalten. Kern-Check bestätigt. Vorbehalte: die drei Punkte „angenommen vorbehaltlich Team“.
