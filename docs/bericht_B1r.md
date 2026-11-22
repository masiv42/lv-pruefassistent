# Bericht B1r – Risikobericht für Kalkulatoren lesbar (L43)

Stand: 21.11.2026, Branch arbeit/B1r. Rollenkette E1 vor dem Code: docs/uebergabe.md (Commit 384d37a).
Anlass: Export „Risikobericht_Abgabe_LV_2026-11-21“ (Stand 1c030c4-dirty, vom Team erzeugt) – Zahlen ohne
Bezeichnung und Einheit, nicht zuordenbar.

**Kern-Check:** Punkte 1–6 eingehalten. Die Funde sind unverändert (456), es werden nur Werte der Position
übernommen. Es gibt keine eigene Rechnung und keine Preisbewertung (E9). Der Beleg-Status spricht nicht von
Personen (Kern 3). Die KI-Spalten bleiben mit Warnhinweis erhalten (E13). Die Prüfsummen bleiben beide, die
Reduktion ist ein Vorschlag (F2). Vom Prioritäten-Auditor bestätigt (Abschnitt 5).

## 1. Änderungen (nur src/bericht.py und Tests)

- **Blatt „Funde“:**
  - Spalte „Nr.“ vorn: laufende Nummer in Sortierreihenfolge (E14: bei gleicher Eingabe gleich).
  - Stufe als Text („1 – Fehlerprüfung“ …).
  - Direkt nach dem Kurztext: Menge, Einheit, EP (€), GP (€) aus der Position (parse()). Bei mehreren
    Positionen (Nr. 4) gilt die erste. Leer, wenn die Position unbepreist ist. Zahlen als Zahl, Format wie im
    LV: Menge mit 3 Nachkommastellen, EP mit bis zu 3, GP mit 2.
  - Rang ganz hinten als „Rang der Prüfung in der Stufe (1 = zuerst)“. Das war der Vorschlag von Oberfläche &
    Bericht: Die Zeilen sind schon danach sortiert, vorne lenkt die Zahl ab.
  - Alle Überschriften umbrochen, Kopfzeile drei Zeilen hoch.
- **Blatt „Übersicht“:**
  - Oben „Für den Kalkulator“: Datei, Zeitpunkt, Format, Positionen, Funde gesamt, je Stufe und je
    Kategorie, Sortierung, Datei-Hinweise, Prüfabdeckung.
  - Unten „Prüfstand (technisch)“: Prüfungen, fingerprint, Commit, Versionen, Prompt-Version, SHA-256.
  - Jede Zeile hat eine Klartext-Erklärung in Spalte C.
- **Warnzeile:** Endet der Commit auf „-dirty“, steht oben „WARNUNG – Prüfstand nicht committet – nicht für
  Abgabe oder Demo verwenden“.
- **KI-Warnhinweis:** im Wortlaut des Teams, ohne Dateipfad; gilt auch für die Detailansicht der App (gleiche
  Konstante).
- **Beleg-Status** (nach docs/pruefprotokoll.md, S2: Prüfskript liest nur das Original, ohne parse()):
  - „Zitat wörtlich im Original bestätigt (automatische Prüfung, unabhängig vom Parser; keine fachliche
    Bewertung)“
  - „Zitat aus der automatischen Auswertung; Abgleich mit dem Original steht für diesen Fund noch aus“
  - „Zitat steht so nicht wörtlich im Original“
- **Neues Blatt „Legende“:** jede Spalte in einem Satz, die Stufen 1–4, Rang, Einheiten, Beleg-Status und die
  KI-Spalten (die KI entwarnt nie, E13). Auch eine reine Preisdatei bekommt die Legende.

## 2. Skeptiker am Original (Abgabe LV.pdf)

6 Funde: Menge, Einheit, EP und GP im Bericht gleich der Mengenzeile im Block der jeweiligen OZ.

| Nr. | OZ | Seite | Bericht | Original |
|---|---|---|---|---|
| 1 | 3.3.3 | 38 | 85,000 m · 80,04 · 6.803,40 | „85,000 m 80,040 6.803,40“ |
| 2 | 3.3.4 | 38 | 60,000 m · 98,47 · 5.908,20 | „60,000 m 98,470 5.908,20“ |
| 3 | 5.3.3 | 53 | 2,000 m · 80,04 · 160,08 | „2,000 m 80,040 160,08“ |
| 4 | 1.1.4 | 21 | 1,000 St · 560,00 · 560,00 | „1,000 St 560,000 560,00“ |
| 5 | 2.1.1 | 28 | 1,000 psch · 200,00 · 200,00 | „1,000 psch 200,000 200,00“ |
| 6 | 2.1.4 | 28 | 1,000 psch · 400,00 · 400,00 | „1,000 psch 400,000 400,00“ |

Das Original druckt den EP mit drei Nachkommastellen; das EP-Format zeigt deshalb bis zu drei.

## 3. Tests (src/test_bericht.py, B1r)

- Überschriften umbrochen und lesbar.
- „Nr.“ ist 1 … n.
- Stufe als Text.
- Legende mit allen Spalten, Stufen und dem Beleg-Status.
- Kein „data/“ in einer Zelle.
- Menge, EP und GP gleich parse() bei Abgabe LV.pdf (9 Funde).
- Übersicht zweigeteilt, mit Erklärung je Zeile, und die Erklärungen passen zur Zeile.
- Warnzeile nur bei „-dirty“.
- Beleg-Status ohne „Person“ oder „Mensch“.
- Gleiche Eingabe, gleiches Blatt (E14).

Angepasst wurden die bisherigen Tests (Blätter, Rang-Spalte, Warnhinweis-Text, Beleg-Status). test_bericht
67/67, alle anderen Testreihen grün, Doppellauf 13/13.

Browser (lv-app-agent, Mini-Auszug [ORT_024] LV24069.D86): Seite mit Download-Knopf ohne Fehler aufgebaut (der
Bericht wird dabei erzeugt), Stufe 4 sichtbar, keine Serverfehler.

## 4. Kalkulator-Urteil (E2 (h)) [ANNAHME, simulierte Praxissicht]

Export von Abgabe LV.pdf: **ohne Erklärung verständlich**.
- Jede Zeile nennt Stufe in Worten, OZ, Kurztext, Menge mit Einheit und den Preis aus dem LV; „Befund“ und
  „Zitat/Beleg“ stehen daneben.
- Oben steht, was ich wissen muss; die Technik steht unten und ist erklärt.
- Die Legende beantwortet die Fragen, die ich sonst gestellt hätte.

Offen aus meiner Sicht: Zwei Prüfsummen sind für mich eine zu viel (F2).

## 5. Prioritäten-Auditor – Abnahme

Geprüft:
- Abnahmekriterien des Teams, alle als Test vorhanden und grün.
- Funde und Fundzahl unverändert (456).
- Skeptiker: 6 Werte am Original.
- Doppellauf 13/13.
- E11: 44/44 Prüfsummen. E12 (4): data/findings leer.

**B1r abgenommen mit Vorbehalt F2** (Prüfsummen; betrifft nur die Übersicht, nicht B1c).
