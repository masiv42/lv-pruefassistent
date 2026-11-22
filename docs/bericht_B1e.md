# Bericht B1e – Nr. 17 Rechenprüfung Menge × EP und Prüfer-Zuordnung

Stand: 21.11.2026, Branch arbeit/B1e. Rollenkette E1 vor dem Code: docs/uebergabe.md (Commit 1fdba0e).

**Kern-Check:** Punkte 1–6 eingehalten. Der Beleg sind Menge, EP und GP der Position. Es gibt keine
Preisbewertung (E9). Kein KI-Einfluss, der Doppellauf ist grün. Die Prüfer-Zuordnung ist als Vorschlag markiert
(F1). Vorher: E11-Abweichung angehalten und gemeldet (FS1), vom Team um 22:15 behoben.

## Ergebnis

- **Regel** (src/pruefung_rechnung.py):
  - |Menge × EP − GP| > 0,01 € + |Menge| × 0,0005 € ergibt einen Fund: nachweisbarer Fehler, Stufe 1, Rang 1.
  - Toleranz: Der GP ist auf Cent gerundet (≤ 0,005 €), der EP ist höchstens mit 3 Nachkommastellen gedruckt
    (≤ 0,0005 € je Einheit). Was darüber liegt, erklärt keine Rundung.
  - Die Prüfung läuft auch in reinen Preisdateien (D84).
- **Datensatz (Messung):**
  - 1.242 Positionen nachgerechnet: Abgabe LV.pdf 248, Angebot AN24-0305.D84 274, Angebot AN24-0305.pdf 274,
    StBALV23040.D86 249, [ORT_024] LV24069.D86 197.
  - **0 Abweichungen**; die größte Differenz ist 0,0018 € (Angebot 2.3.40, Rundung des GP).
  - StBALV23040.D84 hat Preise ohne Menge: 0 nachgerechnet.
- **Ausgabe:** Fundzahl unverändert 456.
  - App-Kopf, auch bei reinen Preisdateien: „Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“.
  - Export: Zeile „Prüfabdeckung Nr. 17“, z. B. „Rechenprüfung: 248 Positionen nachgerechnet, 0 Abweichungen“.
- **Prüfer-Zuordnung** (bericht.PRUEFER, Vorschlag): Spalte „Prüfer“ in App-Liste, Detail und Export; Legende.

  | Prüfer | Prüfungen |
  |---|---|
  | Widerspruch | 1, 2, 16 |
  | Formal | 3, 4, 15 |
  | Mengen | 5, 6, 13, 18 |
  | Nachtrag | 7–10 |
  | Klarheit | 11, 12, 14 |
  | Preis | 17 |
  | Vollständigkeit | 19 |
  | Tippfehler | B5 (KI) |

## Skeptiker am Original (ohne parse())

| Datei | OZ | Original | Menge × EP | GP | Abweichung |
|---|---|---|---|---|---|
| Angebot AN24-0305.pdf | 2.3.40 (S. 8) | „545,270 m³ 0,34 185,39“ | 185,3918 | 185,39 | 0,0018 € |
| Angebot AN24-0305.D84 | 2.3.40 | Satz 21 „00000545270m“, Satz 23 „00000000340 000000018539“ | 185,3918 | 185,39 | 0,0018 € |
| Abgabe LV.pdf | 3.2.3 (S. 34) | „1.140,000 m3 145,880 166.303,20“ | 166.303,20 | 166.303,20 | 0 |
| StBALV23040.D86 | 03.03.0003 | Satz 21 „00000085000m“, Satz 23 „0000008004 000000680340“ | 6.803,40 | 6.803,40 | 0 |
| [ORT_024] LV24069.D86 | 06.02.1 | Satz 21 „00000005000St“, Satz 23 „0000291928 000001459640“ | 14.596,40 | 14.596,40 | 0 |

## Tests

- src/test_pruefung_rechnung.py, 16 Tests:
  - erfundene Mini-Datei mit einer Abweichung (3 × 1.200 ≠ 3.800), Rundungsfall 0,0018 €, Menge 0, unbepreist;
  - reine Preisdatei; Prüfabdeckungstext; Rang 1; Prüfer; E14;
  - Messung am Datensatz.
- Angepasst: test_pruefabdeckung (Nr. 17 als Eintrag) und test_bericht (Rechenprüfungszeile, Spalte „Prüfer“). Alle Testreihen grün (test_bericht 69/69), Doppellauf 13/13, Durchlauf 43 OK, 0 FEHLER, E11 44/44.

## Kalkulator-Urteil [ANNAHME]

**Nützlich.** „Rechenprüfung: 248 Positionen nachgerechnet, 0 Abweichungen“ sagt mir, dass nachgerechnet wurde.
Der Prüfer je Fund hilft beim Verteilen im Team.

## Prioritäten-Auditor

Abnahmekriterien erfüllt: Mini-Datei mit Abweichung, 5 Positionen am Original, Ausgabe auch bei 0, Prüfer in
App und Export. Testreihen, Doppellauf, Durchlauf und E11 stehen in docs/uebergabe.md.
**Abgenommen mit Vorbehalt F1** (Prüfer-Zuordnung, nicht blockierend).

**Nachtrag (Sitzung B4, 21.11.2026):** F1 vom Team mit „ja“ beantwortet (23:55). Die Zuordnung oben gilt als
festgelegt, der Vorbehalt ist erledigt (docs/decisions.md).
