# Challenge A – Vorgaben und Umfang

Originaltext: input/challenge_A_offiziell.md (maßgeblich, hier nicht kopiert).
Frühere Team-Fassung ohne Meilensteine und Deliverables:
input/challenge_A_original.md (nur noch zur Nachverfolgung).
Stand: 21.11.2026.

## Ziele laut Challenge-Text [BESTÄTIGT, input/challenge_A_offiziell.md, „Challenge Objective“]
- LV importieren und parsen („PDF, GAEB, Excel“)
- Fehlererkennung mit Priorität: fehlende Positionen („missing items“),
  unklare Beschreibungen, Widersprüche, Tippfehler
- Risikobewertung: unpräzise Leistungsbeschreibungen, ungewöhnliche Mengen
- Nachtragspotenzial und wahrscheinliche Streitpunkte in der Ausführung
  erkennen
- Optional: Einheitspreise oder Zuschläge aus historischen Projektdaten

## Meilensteine [BESTÄTIGT, input/challenge_A_offiziell.md, „Milestones“]
1. LV parsen und strukturiert extrahieren
2. Fehlererkennung und Plausibilitätsprüfungen
3. Risikobewertung und Erkennung von Nachtragspotenzial
4. Historische Projektdaten einbinden (optional)
5. What-if-Analysen („material prices, alternatives“)

## Deliverables [BESTÄTIGT, input/challenge_A_offiziell.md, „Deliverables“]
- „Demo of a web app or assistant tool with upload and risk report“
- „Pitch from an estimator's perspective: How does the prototype change the
  bidding process?“

## Daten laut Challenge-Text [BESTÄTIGT, input/challenge_A_offiziell.md, „Data“]
- Anonymisierte Beispiel-LVs verschiedener Gewerke und Projektgrößen
  („GAEB preferred“); liegen in data/raw/
- Optional: historische Projektdaten, reale Beispiele fehlerhafter
  LV-Positionen, Einheitspreis-Kataloge – wo diese liegen, ist eine Frage an
  die Orga [OFFEN, docs/open-questions.md]

## Umfangsentscheidungen des Teams [BESTÄTIGT, Team, Chat 21.11.2026; docs/decisions.md]
- Export des Risikoberichts: Pflichtumfang (Deliverable).
- Meilenstein 4 (historische Daten): ausgeschlossen.
- Meilenstein 5 (What-if): Entscheidung nach P2 und Risikobericht [OFFEN].
- Fehlende Positionen: nach P2 und Risikobericht als Risikohinweis
  „mögliche fehlende Leistung“ mit höchstens 5 Paarregeln
  (docs/guardrails.md, Abschnitt D).
- Nachtragspotenzial: nur als „mögliches Nachtragspotenzial“ bzw.
  „möglicher Streitpunkt in der Ausführung“; nie „Anspruch“, „berechtigt“,
  „durchsetzbar“, keine Paragraphen-Verweise (R7).
- Excel-Import: ausgeschlossen, solange die Orga keine Beispieldatei liefert.

## Rahmen [BESTÄTIGT, bmad_prompt.txt]
- Abgabe: Sonntag, 22.11.2026, 12:00 Uhr
- Team: zwei Personen
- Nutzer: kalkulierende Person eines ausführenden Unternehmens
- Der Bieter darf das LV nicht ändern; Unklarheiten klärt er über
  Rückfragen an den Auftraggeber.

## Abgrenzung
Was der Prototyp abdeckt und was nicht: docs/guardrails.md, Abschnitt D.
Offene Fragen: docs/open-questions.md.
