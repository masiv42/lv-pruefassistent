# Bericht B1p – Parser-PDF: Langtext nur aus dem Text der Position (mit Vorlauf F1, F2, F4 aus B1b)

Stand: 21.11.2026, Branch arbeit/B1p. Rollenkette E1 vor dem ersten Code-Schritt: docs/uebergabe.md (Commit
bb55188, vor dem ersten Code-Commit 060e32a).

**Kern-Check:** Punkte 1–6 eingehalten. Belege stammen aus dem Text der Position und sind am Original
geprüft. Die Kategorien bleiben R6. Status setzt nur der Mensch. Kein KI-Einfluss. Der Doppellauf ist grün.
Gearbeitet wurde an B1p und am Vorlauf aus den Teamantworten F1/F2/F4; die Rollenkette stand vor dem Code.
Vom Prioritäten-Auditor bestätigt (Abschnitt 6).

## 1. Vorlauf: F1, F2, F4 (Commit 060e32a)

- **F1:** In Dateien der Austauschphase 86 mit Menge 0 und leerer Einheit gilt jetzt: Kategorie Unklarheit,
  Stufe 4, Rang 1, Titel „Ohne Menge und Einheit (Auftrags-LV)“, Text „Position im Auftrags-LV ohne Menge und
  Einheit – Abrechnungsgrundlage klären. Empfehlung laut Prüfkatalog: vormerken.“ Betroffen sind 38 Funde in
  [ORT_024] LV24069.D86. In Ausschreibungs-LVs bleibt „Einheit fehlt“ in Stufe 1 (Tests mit .D83/.X83/PDF).
  Skeptiker am Original (Satz 21: Menge `00000000000`, Einheit leer; Satz 23 mit EP): 8.1.1, 8.2.1, 8.3.1,
  8.5.1, 8.6.8. Die Reihenfolge ändert sich nur in dieser Datei: die 38 Funde stehen jetzt hinter Stufe 2.
- **F2:** Bei einer Bedarfsposition gibt es keinen eigenen „Menge 0“-Fund mehr. Der Nr.-5-Fund trägt den
  Feldwert „Menge: 0“ und den Satz „Die Menge ist 0.“. Die Fundzahl sinkt von 464 auf 459. Entfallen sind
  LV_00_Roh_und_Erdauarbeiten.pdf 3.1.340, 3.1.350, 3.1.360 und LV_13_ELT.pdf 1.3.2.35, 1.3.2.36. Alle 5 sind
  am Original „*** Bedarfsposition ohne GB“ mit „0,000 … Nur Einh.-Pr.“ (LV_00 S. 32/33, LV_13 S. 19).
- **F4:** data/findings/LV_17_Trockenbau.pdf.json liegt jetzt in archiv/findings/. Die Datei ist nicht
  gelöscht, data/findings ist leer.

## 2. B1p – Befunde am Original und Korrektur (nur PDF-Zweig von src/lv_parser.py)

| Befund am Original | Korrektur |
|---|---|
| Angebot AN24-0305.pdf (einziges PDF mit Menge in der OZ-Zeile): Positionstext eingerückt; Fußzeile mit Bankdaten (S. 1), „Hinweistext …“, „Zusammenstellung Bereich n.“ auf Höhe der OZ-Spalte; Kurztext bis 2 Zeilen | eingerückte Zeilen = Kurztext (zusammengefügt), kein Langtext; Zeile auf Höhe der OZ-Spalte beendet den Positionstext |
| Schluss der LVs LV_01–LV_23: „Zusammenstellung“, „Zuzüglich der gesetzlichen Mehrwertsteuer …“, Unterschrift, „Das LV besteht aus den Seiten …“ am Langtext der letzten Position | diese Zeilen beenden den Positionstext bis zur nächsten OZ (`STOP_RE`) |
| Kopfzeilen kurzer PDFs (LV_01, LV_15, LV_15a; 2 Seiten: Firma, Tel./Fax, „Projekt: …“, „LV: …“) mitten im Langtext | Zeilen, die im Kopfbereich (erste 12 Zeilen) jeder Seite gleich stehen, sind Kopfzeilen (bisher erst ab 4 Seiten) |
| Leistungsverzeichnis.pdf, LV_00, LV_04, LV_14 u. a.: Kurztext in eigener Schrift (z. B. F1), Langtext F2; umbrochene zweite Kurztext-Zeile in F1 landete im Langtext (2.1.410 „bis DN 300“, 1.1.140 „und entsorgen“) | Folgezeilen in der Kurztext-Schrift gehören zum Kurztext, wenn diese Schrift nicht die Langtext-Schrift ist; nicht bei Zeilen mit Platzhalter (im Datensatz ganz in anderer Schrift neu gesetzt) und nicht bei Überschriften („Hinweis:“, „Hinweis für …“) |

Parser-Ausgabe vorher/nachher über alle 34 PDFs: OZ-Listen, Mengen, Einheiten, EP, GP und Seiten sind
unverändert. Geändert haben sich 215 Kurztexte, 44 Langtexte und 14 Titeltexte. validate_parser zeigt
dieselben Werte wie vorher.

**Stichprobe außerhalb der Gegenproben** (Schrift jeder Zeile am Original): LV-Schachtbauwerk.pdf 5.2.30,
5.3.10, 5.3.70, 5.3.210; LV_13_ELT.pdf 1.2, 2.1; LV_14_Sanitaeranlage.pdf 2.29, 3.2;
LV_00_Roh_und_Erdauarbeiten.pdf 3.1.450; LV_08_Fliesen_und_Natursteinarbeiten.pdf 13.2.14. In allen Fällen
steht die angehängte Zeile in der Kurztext-Schrift F1, danach beginnt der Langtext in F2; in LV_13 und LV_14
wiederholt der Langtext den zweizeiligen Kurztext wörtlich. LV-Schachtbauwerk.pdf hat dieselben OZ wie das
Angebot: Kurztext gleich in 27 von 28 Positionen, die Ausnahme ist 5.3.30 (Platzhalter, L45). Die
Prüfabdeckung dort sinkt von 23 auf 17, weil 6 Positionen nur einen zweizeiligen Kurztext haben (z. B. 5.3.10:
„… FF DN“ / „300/1000 mm lg mit Mauerflansch“, beide F1, danach die Mengenzeile).

**Gegenproben am Original:**
- Kurztext Angebot = Leistungsverzeichnis.pdf (dieselbe LV, das Angebot druckt nur Kurztexte): 272 von 274
  (vorher 246).
- Kurztext PDF = GAEB XML derselben LV: Leistungsverzeichnis_leer.pdf und Abgabe LV.pdf je 233 von 248
  (vorher 209); HEM2301-2_Gesamt-LV.pdf 116 von 159 (vorher 117; eine bekannte Abweichung, 03.02.1).
- Grenzen: L45.

## 3. Änderungen der Funde (459 → 457), je Datei und Prüfung

| Datei | Prüfung | Änderung | Begründung am Original (Skeptiker) |
|---|---|---|---|
| Angebot AN24-0305.pdf | Nr. 1 | −2.1.410, −4.1.200 | Kurztext zweizeilig (4.1.200 S. 18: „… > DN 50 bis“ / „DN 300“), kein Langtext gedruckt; kein Widerspruch Kurz-/Langtext möglich |
| Leistungsverzeichnis.pdf | Nr. 1 | −2.1.410, −4.1.200 | S. 15 bzw. S. 44: „bis DN 300“ steht in der Kurztext-Schrift F1 (Langtext F2); bisher als Langtext gelesen |
| Leistungsverzeichnis.pdf | Nr. 1 | +5.3.210 | S. 64: Kurztext „… h bis 60 cm, bis DN 250“ (zweite Zeile „DN 250“ in F1); Langtext „… für Nennweite bis DN 300“. Bisher stand „DN 250“ im Langtext, mit zwei DN-Werten im Langtext meldet die Regel nichts. Bereichsangabe → B1q (L41) |
| LV-Schachtbauwerk.pdf | Nr. 1 | +5.3.210 | S. 13: Kurztext „… bis“ / „DN 250“ (zweite Zeile F1), Langtext „… für Nennweite bis DN 300“; beide Belege wörtlich auf S. 13 |
| LV_04_Porenbetonfassade.pdf | Nr. 5 | Beleg 9.1.90, 9.1.100 | S. 2: zweite Kurztext-Zeile in F1 („konsolen bzw. Abfangkonsolen“, „stielen bzw. Stützenverlängerungen.“); der Langtext (F2) beginnt danach |
| LV_14_Sanitaeranlage.pdf | Nr. 5 | Beleg 4.12, 4.13 | S. 31: zweite Kurztext-Zeile in F1 („PARADISE FOAM SLIM“, „PARADISE PAPER SLIM“) |

Alle Belege der 2 neuen und 4 geänderten Funde stehen wörtlich auf einer Seite des Originals: geprüft am
Seitentext (5.3.210 in beiden Dateien) bzw. an der Schrift der Zeilen (LV_04 S. 2, LV_14 S. 31). test_pruefung
deckt davon nur Leistungsverzeichnis.pdf ab; LV-Schachtbauwerk.pdf liegt nicht in seiner Dateimenge. Die Reihenfolge ändert sich in Angebot AN24-0305.pdf,
LV-Schachtbauwerk.pdf und Leistungsverzeichnis.pdf (Funde entfallen bzw. kommen hinzu). Formatvergleich: neue
bekannte Abweichung 5.3.210 (Leistungsverzeichnis.pdf / Angebot) mit Beleg am Original in
src/test_reproduzierbarkeit.py.

**Prüfabdeckung neu gezählt (Nr. 1/2):** Angebot AN24-0305.pdf 0 von 274 (vorher 67, L38);
Leistungsverzeichnis.pdf 172 von 274 (vorher 202); LV-Schachtbauwerk.pdf 17 von 28 (vorher 23); alle anderen
Dateien unverändert.

Zahlen nach B1p: 457 Funde (Nr. 1: 22, Nr. 2: 13, Nr. 3: 44, Nr. 5: 162, Nr. 6: 216); Stufe 1: 35,
Stufe 2: 384, Stufe 4: 38.

## 4. Tests

Neu ist src/test_parser_pdf.py (20 Tests). Die Einzelfall-Tests haben Erwartungswerte aus dem Original
(Seitentext, Schrift der Zeile) und prüfen, dass der Text auf der Seite steht. Die Schwellen der Gegenproben
(mindestens 233 bzw. 116 gleiche Kurztexte) und die Listen bekannter Abweichungen sind Regressionsschutz,
abgelesen am Stand nach B1p, nicht aus dem Original abgeleitet. Angepasst mit Begründung im Code: test_pruefung (Stufe 1: 13, Stufe 2: 15), test_pruefung_formal
(F1/F2-Tests, S2-Abgleich mit entfallenen Funden), test_bericht (LV_00 68, Angebot 0 von 274),
test_pruefabdeckung, test_reproduzierbarkeit (bekannte Abweichung 5.3.210).

## 5. Kalkulator-Urteil (E2 (h)) [ANNAHME, simulierte Praxissicht]

- F1, Auftrags-LV in Stufe 4: **nützlich**. Stufe 1 ist jetzt frei von 38 Formalfällen.
- F2, Bedarfsposition mit Menge 0 als ein Fund: **nützlich**.
- B1p, Parser: **nützlich**. Zwei Fehlalarme wegen umbrochener Kurztexte sind weg. Ein echter Prüfpunkt
  (5.3.210: Kurztext bis DN 250, Langtext bis DN 300) war vorher verdeckt. „Angebot: prüfbar in 0 von 274“
  sagt ehrlich, dass das Angebot-PDF für Nr. 1/2 nichts hergibt.

## 6. Prioritäten-Auditor – Abnahme

Geprüft:
- Fundzahl 464 → 459 nur durch F2 (5 Fälle, E5-Eintrag); 459 → 457 durch B1p, jede Änderung oben je Datei und
  Prüfung erklärt und am Original geprüft.
- F1 ändert nur Stufe, Kategorie, Titel, Text und Empfehlung von 38 Funden; die Fund-IDs bleiben.
- Alle Testreihen grün; Doppellauf 13/13, drei Läufe byte-gleich.
- E11: 44/44 Prüfsummen, 44 Dateien. E12 (4): data/findings leer.
- Lücken: L34, L38, L39, L40 erledigt; L41 teilweise erledigt, Rest in B1q; neu L45 (Grenzen).

Nachtrag: Die Skeptiker-Prüfung aller entfallenen und neuen Funde am Original (LV-Schachtbauwerk.pdf
5.3.210, 4.1.200 in beiden Dateien) und die Stichprobe außerhalb der Gegenproben sind nachgeholt (Abschnitt 2
und 3); vorher stützte sich die Abnahme dort auf test_pruefung, das LV-Schachtbauwerk.pdf nicht abdeckt.

**B1p abgenommen.** Nächster Block nach der Reihenfolge: B1q. Er nutzt die Zahlen nach B1p (22 Funde Nr. 1).
