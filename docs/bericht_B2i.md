# Bericht B2-Integration (Meilenstein) – Sitzung B1

Stand: 21.11.2026, Branch arbeit/B2i. Rollenkette vor dem Code: docs/uebergabe.md (Commit 5144b21).

**Kern-Check:** Punkte 1–6 eingehalten, mit einem offenen Befund zu Punkt 1 (FS2, F2): In einigen PDFs hängt der
Parser Text hinter der Mengenzeile an die vorige Position. Funde, die sich darauf stützen, zitieren zwar wörtlich
aus dem Original, aber nicht aus dem Text dieser Position. Der Befund ist am Original belegt und als bekannte
Abweichung geführt; die Behebung ist für B1p2 vorgeschlagen.

## Ergebnis

- **a) Prüfungen:**
  - alle_pruefungen() liefert Nr. 1–19.
  - Die Ränge kommen nur noch aus der zentralen Tabelle; die Module lesen PRIORITAET_IN_STUFE.
  - Namen Nr. 1–19 im Bericht (FS-B2-9).
  - Prüfabdeckung Nr. 1–19; Katalogzeile Nr. 19.
- **b) Nr. 16 am Original:** Alle 4 Gruppen liegen je im selben Abschnitt.
  - LV_00 3.2.100 und 3.2.195 unter „3.2. Stahlbetonfertigteile“ (S. 40).
  - LV_08 13.2.6/13.2.30 und 13.2.7/13.2.40 unter „13.2. Fliesenarbeiten …“ (S. 5).
  - LV_14a ist ohne Titel.
  - Die B1p-Titeländerungen sind richtig: Die zweite Titelzeile steht in der Titelschrift F1, z. B. „Hallenstützen und
    -binder“. Gruppen ändern sich dadurch nicht.
- **c) App, Export, Belegprüfung:**
  - App: Stufe 1 offen, Stufen 2–4 je Prüfung aufklappbar mit Anzahl; Prüfabdeckung im Kopf zusammengefasst.
  - Export: Legende mit Prüfer und Kostenwirkung je Prüfung.
  - Belegprüfung von Sitzung B2 übernommen, 1.076 Funde: „bestätigt“ nur für GAEB XML, PDF und GAEB-90-Kurztexte.
  - Ausgelassen: 158 GAEB-90-Funde mit Langtext-Ausschnitt (bleiben „Abgleich steht aus“, B2-L1) und 1 Fund, dessen
    Beleg nicht im Original stand.
- **d) Bieterfragen:** Knopf „Bieterfragen (Entwurf, .xlsx)“ neben dem Risikobericht, in der korrigierten Fassung
  (Auswahl nach Empfehlung, keine Fragen für Auftrags-LVs). Im Durchlauf entstehen 40 Entwürfe.
- **e) Excel:** Upload mit Spalten-Zuordnung, Kennzeichnung „Excel-Import: ohne Orga-Beispiel getestet“.
- **f) Seiten:** „Uebersicht“ (Sitzung B2) und „Zuschlag und What-if“ (dünne Seite um src/seite_zuschlag.py);
  session_state-Schlüssel laut Vorschlag.
- **g) Vergleichspreise:** in der Detailansicht, immer mit Quelle (Datei, OZ, EP); D84 nicht verknüpft.
- **h) Demo:** `demo/` steht in .gitignore. Demo-LV erzeugt (`demo/Demo-LV_B7_[PROJEKT_004].X83`). KI-Cache für
  die 2 Nr.-1/2-Funde gefüllt, mit 2 Groq-Aufrufen; beide Einordnungen „echter Widerspruch“, danach aus dem Cache.
- **i) Doku:**
  - Katalog Nr. 7–19 (Treffer, Rang, Kostenwirkung, Status).
  - Abdeckung.
  - Lücken B2-L1 bis B2-L9.
  - Fehlschläge FS-B2-0 bis FS-B2-10.
  - Lehren in AGENTS.md „Known pitfalls“.
  - Entscheidungen, Backlog, Datenvertrag.

## Prüfung

- **Fundzahl:** 1.688 (Nr. 1: 21, 2: 13, 3: 44, 5: 162, 6: 216, 7: 223, 8: 178, 9: 168, 10: 181, 11: 79, 12: 317,
  13: 45, 14: 1, 15: 3, 16: 4, 18: 32, 19: 1).
- **Durchlauf:** 43 OK, 1 HINWEIS (.docx), 0 FEHLER.
- **Goldstandard:** Die 22 Funde der 7 echten Widersprüche liegen alle in Nr. 1/2. Diese Regeln sind unverändert;
  der S2-Abgleich in test_pruefung_formal ist grün.
- **Testreihen Sitzung B2 (auf dem integrierten Stand):** Hinweise 82/82, Struktur 45/45, Vollständigkeit 30/30,
  Excel 19/19, Zuschlag 22/22, Vergleichspreise 25/25, Demo 25/25, Bieterfragen 22/22, Rückblick 2/2,
  Übersicht 14/14, B5-Fälle Exit 0.
- **Testreihen Sitzung B1:** alle grün (test_bericht 69/69 nach Anpassung der Zahlen an 1.688 Funde).
- **Doppellauf:** siehe docs/uebergabe.md (FS2: Formatvergleich; Ursachen am Original belegt).
- **Browser (lv-app-agent, erfundene Mini-Datei .xlsx und Auszug .D86):**
  - Excel-Kennzeichnung sichtbar; Nr. 17 findet die eingebaute Abweichung (10 × 5 ≠ 60); Nr. 1 gefunden.
  - Stufe 3 gruppiert; Detailansicht „Prüfung Nr. 17 (Prüfer: Preis)“ mit Feldwerten; Vergleichspreise.
  - Übersichtsseite mit Funden je Stufe und Downloads; Zuschlagsseite mit allen Werten auf 0 und Hinweis E9.
  - Keine Serverfehler.
- **Hinweis zur Übersichtsseite:** Sie zeigt „Positionswert laut LV (Summe GP) – kein Risikobetrag“. Das ist eine
  Summe aus dem LV, keine Bewertung; bitte mit E9/R11 abgleichen.

## Kalkulator-Urteil [ANNAHME]

**Nützlich.** Stufe 1 bleibt oben offen. Die über 1.200 Hinweise liegen zusammengeklappt mit Anzahl darunter. Die
Bieterfragen sind ein guter Startpunkt.
**Rauschen-Risiko:** Nr. 12 Verweistext (317) und Nr. 7 (223) sind viel; die Gruppierung hält sie aus dem Weg.

## Prioritäten-Auditor

Abgenommen mit Vorbehalt F2 (Text hinter der Mengenzeile im PDF, FS2). Nicht blockierend: Die Abweichungen sind am
Original belegt und dokumentiert; die Behebung ist für B1p2 vorgeschlagen.
