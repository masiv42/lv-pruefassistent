# Bericht M2-Paket – KI-Blatt, Nachtrag und Streitpunkte, Erfahrungsdatenbank

Stand: 22.11.2026, 03:25, Branch arbeit/M2, geprüfter Code-Stand 43d0e66.

**Kern-Check:** Punkte 1–5 eingehalten. **Abweichung Punkt 6 (E1):** Scope-Wächter, Auditor-Auftrag und Kalkulator-Erwartung standen für M2, M2b und M2c nicht vor dem Code in docs/uebergabe.md; sie sind dort als „nachgetragen“ gekennzeichnet. Deshalb ist das Paket noch nicht auf main (F1 in docs/uebergabe.md).

## Ergebnis

| Block | Gebaut | Prüfung |
|---|---|---|
| M2 | Blatt „KI-Vorschläge“ (src/ki_blatt.py): getrennt von den Regel-Funden, Warnhinweis E13, Quelle, Modell, Prompt-Version, nur aus dem Cache | test_ki_blatt 21/21; Blatt „Funde“ mit und ohne KI identisch; Cache-Zitat, das nicht mehr im Text steht, erscheint nicht |
| M2b | Seite und Blatt „Nachtrag und Streitpunkte“ (src/nachtrag_streit.py): zentrale Zuordnung, keine neuen Funde, nur Zählungen | test_nachtrag_streit 34/34; über alle Dateien 1.190 Zeilen, keine R7-Begriffe; Skeptiker 20 von 20 Stichproben wörtlich im Original |
| M2c | Erfahrungsdatenbank (src/erfahrung.py): SQLite, nur aus Klicks auf Bestätigen und Verwerfen, exakter Belegtext, anderes LV | test_erfahrung 30/30; Risikobericht mit und ohne Datenbank identisch; Lesen legt keine Datei an |

Fundzahl unverändert 1.706, Positionen 4.293.

## Zuordnung Abschnitt B (Prüfung gegen input/pruefkatalog.md)

- **Bleiben:** Nr. 1, 2, 16 (möglicher Widerspruch), Nr. 11, 12, 14 (Unklarheit).
- **Fällt heraus (L58):** Nr. 13 Stundenlohnarbeiten. Der Katalog führt sie als „Risikohinweis“; die Kostenwirkung betrifft Verrechnungssatz und Stundenansatz, nicht die Lesart des Textes. Die 43 Funde bleiben in Fundliste und Export.

## Sicherheitsprüfung (L59)

KI-Freitext stammt aus einer Antwort auf fremden LV-Text. App und Export übernehmen deshalb keine KI-Texte mit Link, Kontaktdaten, Markdown-Verweis, Zeilenumbruch oder mehr als 600 Zeichen; zurückgehaltene Vorschläge werden gezählt. Prompt und Prüfkette B5 sind unverändert (E12 (3)).

## Fertig-Check

- 30/30 Reihen auf 43d0e66, Doppellauf 13/13, Durchlauf 43 OK, 1 Hinweis, 0 Fehler, Goldstandard 22/22.
- E11 44/44, data/raw schreibgeschützt, data/findings leer, keine Erfahrungsdatenbank im Projekt.
- Browser (lv-app-agent, Auszug LV_13 S. 48–50 unter zwei Dateinamen): Bestätigen mit Begründung im ersten LV, im zweiten LV „Frühere Entscheidung: bestätigt in auszug_a.pdf, OZ 2.6..1“, Fund dort unverändert offen in Stufe 1; Seite „Nachtrag und Streitpunkte“ mit Hinweistext; keine Serverfehler.

## Angenommen vorbehaltlich Team (00:45, Punkt 3)

- Anzeige-Filter für KI-Freitext (L59). Nachgezählt an echten Antworten: 0 von 36 B5-Cache-Einträgen und 0 von 32 Messantworten werden zurückgehalten.
- „Anderes LV“ heißt anderer Dateiname.
- Begründungsfeld bei jedem Fund in der Detailansicht; es wird nur mit Bestätigen oder Verwerfen gespeichert.

## Grenzen

- L57: Die 30 neuen Funde aus B1p3 und 7|HEM|6.4.1 zeigen weiter „Beleg noch nicht am Original geprüft“ (F2).
- Die Erfahrungsdatenbank enthält auch Testklicks des Teams. Sie muss vor Demo und Abgabe wie die Status nach archiv/ (E12 (4)).
- **Integration UI:** arbeit/M2 und arbeit/ui (5c43080) haben einen Konflikt in src/app.py (`git merge-tree`). Vorschlag: erst M2 auf main, dann holt die Sitzung UI main und löst ihn in ihrem Design-Code.

## Kalkulator-Urteil [ANNAHME]

- **KI-Blatt:** nützlich, weil klar vom Regel-Fund getrennt.
- **Nachtrag und Streitpunkte:** nützlich als Arbeitsliste vor dem Angebot. **Rauschen-Risiko:** Nr. 12 Verweistext ist in Abschnitt B zahlreich.
- **Erfahrung:** nützlich, solange sie nie etwas ausblendet; die Kennzeichnung „kein Beleg“ ist richtig.

## Prioritäten-Auditor

Inhaltlich abgenommen: Tests, Doppellauf, Durchlauf, E11 und Browser sind erfüllt. **Merge auf main erst nach Teamentscheidung zu F1**, weil die Rollenkette nachgetragen wurde.
