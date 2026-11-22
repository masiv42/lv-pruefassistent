# MVP – LV-Prüfassistent

Quelle: bmad_prompt.txt, Abschnitte 1 und 2. Stand: 20.11.2026.

## Nutzer
Kalkulierende Person eines ausführenden Unternehmens.

## Nutzen
Kritische Stellen eines Leistungsverzeichnisses vor der Angebotsabgabe
sichtbar machen, jeweils mit wörtlichem Originalbeleg. Pro Fund optional
eine klärende Rückfrage an den Auftraggeber (keine Rechtsaussage, R7).

## Kernfunktionen (maximal fünf)
1. Import über die vorhandene Parser-Ausgabe (src/lv_parser.py)
2. Positions- und Fundansicht mit Originalbelegen
3. Wenige, klar definierte Prüfklassen (Auswahl aus input/pruefkatalog.md)
4. Bestätigen oder Verwerfen eines Funds
5. Export des Prüfberichts – erst nach funktionierendem Kernablauf

## Erster Durchstich [BESTÄTIGT, Team, Chat 20.11.2026]
Parser-Ausgabe → eine Prüfung → Fund mit Originalbeleg → einfache
Ergebnisansicht.
- Prüfung: möglicher Widerspruch zwischen Kurz- und Langtext bei
  Nennweite (DN) und Betonfestigkeitsklasse (Prüfkatalog Nr. 1 und 2),
  rein regelbasiert und deterministisch.
- Ausgangspunkt: src/heuristik_widerspruch_v0.py.
- Ansicht: kleine Streamlit-App; sie prüft immer genau ein hochgeladenes LV.
- Status Bestätigen/Verwerfen als JSON je LV in data/findings/.
- Eingabe zuerst die 5 Testdateien aus docs/acceptance.md T2, dann alle
  LVs mit je einer Quelle (32 Dateien).

## Nicht-Ziele
Siehe docs/guardrails.md, Abschnitt D, "Nicht im ersten Prototyp".

## Offen
- Zugang zu einer LLM-API für die KI-Gegenprüfung [OFFEN]
