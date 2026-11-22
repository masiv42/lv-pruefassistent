# Bericht B1q – Nr. 1: Mehrfach- und Bereichsangaben

Stand: 21.11.2026, Branch arbeit/B1q. Rollenkette E1 vor dem Code: docs/uebergabe.md (Commit 7a5c78e).

**Kern-Check:** Punkte 1–6 eingehalten. Die Regel ist nur an erfundenen Fällen entwickelt, der Goldstandard
dient nur zur Messung (E12 (3)). Der entfallene Fund ist am Original belegt. Kein KI-Einfluss, der Doppellauf
ist grün. Die Bereichsangaben sind nicht selbst entschieden, sondern als F-Frage gestellt (R2, R10). Vom
Prioritäten-Auditor bestätigt (Abschnitt 5).

## 1. Regel „DN a/b“ (src/pruefung_widerspruch.py)

- „DN a/b“ (auch „DN a / b“, „DN a/b/c“) ist **eine** DN-Angabe mit mehreren Werten. Nennt der Kurztext
  einen dieser Werte, gibt es keinen Fund.
- Die Regel vom 20.11.2026 („Langtext nennt genau eine DN-Angabe“) zählt jetzt Angaben, nicht Werte. So
  bleibt z. B. Kurztext DN 150 gegen Langtext „DN 125/100“ ein Fund; das war schon vorher so.
- Folgt dem zweiten Wert eine Länge („DN 300/1000 mm lg“, „lang“, „Länge“, „Baulänge“), ist er keine
  Nennweite.
- Begründung bei Mehrfachangaben: „Langtext nennt DN 125/100“; sonst unverändert.
- Tests: src/test_regel_dn.py, 12 Tests, nur erfundene Texte.

## 2. Messung am Datensatz (nach der Entwicklung)

- **Goldstandard:** 22 von 22 Funden der 7 echten Widersprüche werden weiter gefunden (vorher 22 von 22).
- **Fundzahl 457 → 456.** Entfallen ist GAEB-[PROJEKT_004].X83 02.0009. Skeptiker am Original (X83, Item
  0009): Kurztext „Rohrauflager und -einbettung, Feinkies 0/32 mm, bis DN 900 mm“, Langtext „01) Kanäle
  DN 800/900 mm“. DN 900 ist in der Mehrfachangabe enthalten, es war ein Fehlalarm.
- **Keine neuen und keine geänderten Funde.** Die Reihenfolge ändert sich nur in GAEB-[PROJEKT_004].X83 (ein
  Fund weniger).
- **Formatvergleich:** Die bekannte Abweichung zu 2.9 (X83 gegen LV-Ausdruck) entfällt, weil es jetzt in
  keinem Format mehr einen Fund gibt.
- **Zahlen nach B1q:** 456 Funde (Nr. 1: 21 in 13 Dateien, Nr. 2: 13, Nr. 3: 44, Nr. 5: 162, Nr. 6: 216).
  Stufe 1: 34, Stufe 2: 384, Stufe 4: 38.

## 3. Bereichsangaben – offen (F1 in docs/uebergabe.md)

Der Auftrag sagt „als Bereich behandeln“, ohne festzulegen, was daraus folgt. Die Fälle 2.1.410 und 4.1.200
sind schon durch B1p entfallen (umbrochener Kurztext). Im Datensatz bleibt 5.3.210 (Leistungsverzeichnis.pdf
S. 64, LV-Schachtbauwerk.pdf S. 13): Kurztext „… bis DN 250“, Langtext „… für Nennweite bis DN 300“.

| Lesart | erfundenes Beispiel | Wirkung auf 5.3.210 |
|---|---|---|
| A: überlappende Bereiche = kein Widerspruch | Kurztext „bis DN 200“, Langtext „bis DN 250“ → kein Fund | entfällt (2 Funde) |
| B: Grenzen vergleichen (heute) | Kurztext „bis DN 200“, Langtext „bis DN 250“ → Fund | bleibt |
| C: wie B, aber in der Begründung als Bereichsangabe gekennzeichnet | „Kurztext nennt bis DN 200, Langtext bis DN 250 (Bereichsangaben, Obergrenzen verschieden)“ | bleibt, mit Hinweis |

Kalkulator [ANNAHME]: 5.3.210 ist ein echter Prüfpunkt, weil die Obergrenze bestimmt, welche Konstruktion
einzupreisen ist. Lesart A würde ihn still entfernen.

## 4. Kalkulator-Urteil (E2 (h)) [ANNAHME, simulierte Praxissicht]

- „DN a/b“: **nützlich**. „DN 800/900“ gegen „bis DN 900“ ist für mich kein Widerspruch.
- Nr. 1 insgesamt (21 Funde): **nützlich**. Die übrigen Fehlalarme (anderes Bauteil: 1.1.4, 2.3.23, 2.3.90,
  3.3.19, .48) bleiben sichtbar; die KI-Gegenprüfung zeigt dort nur einen Hinweis im Detail (E13).

## 5. Prioritäten-Auditor – Abnahme

Geprüft:
- Rollenkette vor dem Code.
- Entwicklung nur an erfundenen Fällen, Messung danach: 22 von 22.
- Ein entfallener Fund, am Original begründet.
- Alle Testreihen grün; Doppellauf 13/13 (456 Funde, drei Läufe byte-gleich).
- E11: 44/44 Prüfsummen. E12 (4): data/findings leer.

**B1q abgenommen mit Vorbehalt F1** (Bereichsangaben). F1 betrifft nur Nr. 1 (Regel in
pruefung_widerspruch.py), nicht B1r (Risikobericht). Nach der stehenden Freigabe kann B1r starten.
