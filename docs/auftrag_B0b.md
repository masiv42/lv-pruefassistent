AUFTRAG B0b – Konsolidierung (Teil B von Block 0). Keine neuen Prüfungen oder Funktionen außer den hier genannten Sicherheitskorrekturen. Ablauf nach docs/guardrails.md E1 mit allen 8 Rollen; es gelten E1–E12.

Erst lesen: AGENTS.md, docs/guardrails.md (besonders E), docs/decisions.md, input/pruefkatalog.md, input/challenge_A_offiziell.md, docs/stand.html, data/qa/ki_messung_lauf1.json; git log --oneline -8; git status. E11 prüfen (Prüfsummen und Anzahl 44), bevor gearbeitet wird.
Zu Beginn: Scope-Wächter und Prioritäten-Auditor prüfen diesen Auftrag, der Kalkulator nennt seine Erwartung. Dateien vorab ansagen.

B0b.1 docs/abdeckung.md (Soll-Ist): eine Zeile je Punkt aus input/challenge_A_offiziell.md (Problem, Goal, Deliverables, Meilensteine) und je Prüfung aus input/pruefkatalog.md, inkl. der früher geplanten, aber weggefallenen Prüfungen (Zulage ohne Grundposition, Doppelpositionen, Widersprüche zwischen Positionen, Tippfehler, OZ-Lücken) und der Prüfungen Nr. 15–18. Spalten: Punkt, Prüfung/Feature, Status (fertig / Light / offen), Beleg (Datei, Test, Commit), Backlog-ID.

B0b.2 docs/backlog.md mit dieser Reihenfolge:
B0 Konsolidierung (dieser Block)
B1 Stufe 1: zuerst L17 – Nr. 1–6 auf Standard E2 nachziehen (Stufe, Handlungsempfehlung, Kostenwirkung, Kalkulator-Urteil); dann Nr. 15 Zulage ohne erkennbare Grundposition, Nr. 16 gleiche Leistung im selben Abschnitt, Nr. 17 Rechenprüfung Menge × EP; Prüfer-Zuordnung (Formal, Widerspruch, Nachtrag, Klarheit, Mengen, Vollständigkeit, Preis, Tippfehler) in App und Export
B2 Stufe 3/4: Nr. 7–10 Nachtragspotenzial, Nr. 11–14 Unklarheiten („vage“ nur in Kombination), Nr. 18 ungewöhnliche Mengen
B3 fehlende Leistungen (höchstens 5 Paarregeln), Bieterfragen-Export, Rückblick-Test mit den Nachträgen aus [ORT_024] LV24069.D86
B4 Excel-Import mit Spalten-Zuordnung
B5 KI: Tippfehler, Widersprüche zwischen Positionen; L11
B6 Vergleichspreise, Zuschlags-Rechner und What-if (Meilenstein 5), Sortierung nach Geld (L7)
B7 Demo-LV (nur Kopie, nie data/raw; mindestens ein Fall je Prüfung inkl. Nr. 4)
B8 Feinschliff; sauberes Snapshot-Repo für die Abgabe (L5)

B0b.3 docs/luecken.md mit L1–L19 (Spalten: ID, Beschreibung, Quelle, Auswirkung, Ziel, Status):
L1 Stufe-1-Prüfungen aus der ersten Planung ohne Begründung weggefallen (Zulage ohne Grundposition, Doppelpositionen, Widersprüche zwischen Positionen, Tippfehler, OZ-Lücken) → B1/B5; OZ-Lücken: Teamentscheidung offen
L2 P4-Rest (Lauf 2, ZDR-Satz, Stand-Bericht) → erledigt (14a762d, 70fb554)
L3 Commit 1548b88 außerhalb des vereinbarten Ablaufs → aufgeklärt (nicht von der Party angelegt, Inhalt geprüft)
L4 Leitplanken D widersprachen der Teamentscheidung → erledigt in B0a
L5 GitHub-Repo mit kompletter Historie inkl. data/raw (privat) → B8 Snapshot-Repo
L6 KI bei echten Widersprüchen unzuverlässig und formatabhängig (3.2.60, 3.3.3, 5.3.3) → Warnhinweis in B0b.6; Ursachenanalyse B5
L7 Sortierung nach Geld innerhalb einer Stufe fehlt → B6
L8 input/pruefkatalog.md nicht synchron mit der Planung → B0b.4
L9 Rollenkette in P2–P4 nicht eingehalten; keine Rolle für Prioritäten, Praxissicht und Kosten → erledigt in B0a
L10 Messtabelle „je Position“ lässt uneinheitliche Positionen weg (zeigt 8/9) → B0b.5
L11 KI wählt nie „unklar“ (0/40), obwohl P4-v2 es im Zweifel verlangt → B5, nur als P4-v3 mit neuen, erfundenen Testfällen (E12 (3))
L12 Meilenstein 5 fehlte im Backlog → erledigt mit B0b.2 (B6)
L13 Alte Ausschluss-Entscheidungen in decisions.md → erledigt in B0a
L14 Fragen an die Orga (Beispiele fehlerhafter LV-Positionen, historische Daten, Preiskataloge, Excel-Beispiel) offen → Team, heute
L15 Stand-Bericht ohne Soll-Ist-Abgleich, Prozess-Abgleich und Abschnitt Agenten-Team → B0b.9
L16 Commits 14a762d und 70fb554 waren nicht gepusht → erledigt in B0a
L17 Prüfungen Nr. 1–6 erfüllen Standard E2 noch nicht → B1 (Anfang)
L18 Parser ohne --out legt eine Datei neben das Original (data/raw) → abgesichert durch E11 (Dateianzahl)
L19 Herkunft der Status in data/findings/ nicht abgesichert (Testklicks könnten im Bericht als Kalkulator-Entscheidung erscheinen) → B0b.7

B0b.4 input/pruefkatalog.md synchronisieren: Die bisherige Spalte „Prio“ (1–4) gilt als Stufe (keine Neubewertung). Die vorhandene Spalte „Empfehlung an die kalkulierende Person“ ist die Handlungsempfehlung. Spalte „Kostenwirkung“ ergänzen (füllt die Rolle Wirtschaft; wo noch nicht bewertet: [OFFEN]). Neue Zeilen mit Status „geplant“ und Treffer [OFFEN] bis zur Datenauswertung:
- Nr. 15 Zulage ohne erkennbare Grundposition – Stufe 1 – nennt die Zulage eine OZ, die es im LV nicht gibt: nachweisbarer Fehler; findet sich im selben Titel keine passende Grundposition: Unklarheit – Empfehlung: Rückfrage stellen – Hinweis: laut Vorprüfung 139 Zulagen im Datensatz, keine verweist per OZ, sondern per Bezeichnung (z. B. „Zulage zur Position GGG Rohr DN 300“) [ANNAHME, Zählung Berater 21.11.2026, in B1 nachprüfen] – Backlog B1.
- Nr. 16 Gleiche Leistung zweimal im selben Abschnitt (gleicher Kurztext, Langtext und Einheit, verschiedene OZ, gleicher unterster Titel; Bedarfs- und Wahlpositionen ausgenommen) – Stufe 1 – möglicher Widerspruch – Rückfrage stellen – Hinweis: laut Vorprüfung 84 Gruppen identischer Positionen in 11 Dateien, viele davon in verschiedenen Abschnitten und damit gewollt [ANNAHME, Zählung Berater, in B1 nachprüfen] – Backlog B1.
- Nr. 17 Rechenprüfung Menge × EP ≠ GP (nur Positionen mit Menge, EP und GP; Toleranz aus der Rundung der Daten ableiten) – Stufe 1 – nachweisbarer Fehler – Rückfrage stellen – Hinweis: Vorprüfung fand in bepreisten GAEB-Dateien keine Abweichung; Nachweis über Tests und Demo-LV – Backlog B1.
- Nr. 18 Ungewöhnliche Mengen (z. B. Menge 1 bei Einheiten wie m, m², m³; auffällig große Vorhaltemengen; konkrete Regeln erst nach der Datenauswertung) – Stufe 2 – Risikohinweis – Risiko einpreisen – [ANNAHME, Regeln in B2 festlegen] – Backlog B2.
Die früher geplanten, aber weggefallenen Prüfungen (Widersprüche zwischen Positionen, Tippfehler, OZ-Lücken) mit Status und Verweis auf L1 aufführen. Nichts löschen.

B0b.5 Messung neu auswerten (L10), ohne einen einzigen KI-Aufruf, nur aus Cache und gespeicherten Zeilen: zusätzlich „je Position, Worst Case“ – eine Position zählt als falsch, wenn die KI in mindestens einer Datei falsch liegt; uneinheitliche Positionen werden so mitgezählt. Gefährliche Richtung je Position getrennt ausweisen. Ergebnis in eine NEUE Datei data/qa/ki_messung_lauf1_auswertung_v2.json; ki_messung_lauf1.json bleibt unverändert. Diese Worst-Case-Zahl ist ab jetzt die Zahl für Bericht und Pitch.

B0b.6 Sicherheitskorrektur L6 (App und Export): Bei KI-Einordnung „anderes Bauteil“ oder „Bereichs- oder Mehrfachangabe“ den Hinweis anzeigen: „KI hält dies für einen möglichen Fehlalarm. Bei echten Widersprüchen war die KI in der Messung vom 21.11. nicht zuverlässig (data/qa/ki_messung_lauf1_auswertung_v2.json) – bitte selbst prüfen.“ Mit Test. Kalkulator-Urteil dazu einholen.

B0b.7 Sicherheitskorrektur L19 (E12 (4)): prüfen, ob Tests oder Browser-Prüfungen in data/findings/ des Projekts schreiben; falls ja, auf Temp-Ordner umstellen (mit Test). Aktuelle Inhalte von data/findings/ auflisten; Status ohne menschliche Herkunft melden und nach archiv/ verschieben, nicht löschen.

B0b.8 Strittige Positionen vorbereiten (keine Entscheidung, R10): 8209.003 05.01.4 – der Skeptiker prüft am Original, ob der Langtext einen Außendurchmesser (139,7 mm) nennt; Daten & Parser sucht eine belegbare Quelle für die Zuordnung Außendurchmesser → Nennweite nach EN 10220 (ohne Quelle: [OFFEN]). 05.01.46: als „Person B prüft erneut am Original“ vermerken. Ergebnis melden; nach der Teamentscheidung wird die Messung aus dem Cache neu ausgewertet.

B0b.9 docs/stand.html aktualisieren (nicht neu schreiben): neuer Abschnitt „Soll-Ist-Abgleich“ (aus docs/abdeckung.md); neuer Abschnitt „Prozess-Abgleich“ (P1–P4: was wie vereinbart lief, was nicht, inkl. 1548b88 und Rollenkette); Abschnitt „Unser Agenten-Team“ mit allen 8 Rollen, Aufgabe, je einem Beispiel, wo die Rolle gewirkt hat, und wo sie hätte wirken müssen, es aber nicht tat; Messung mit der Worst-Case-Zahl aus B0b.5; Grenzen-Tabelle: aufgehobene Ausschlüsse als „geplant in Bx“; Offene Punkte mit Verweis auf docs/luecken.md und docs/backlog.md; neue Regeln E1–E12 in einem Satz je Regel.

B0b.10 Fertig-Check nach E7: E11 (Prüfsummen und 44 Dateien), E12 (4), alle Testreihen, Browser-Prüfung, Kalkulator-Urteil zu B0b.6 und zum Stand-Bericht (verständlich für Nicht-Fachleute?), Auditor-Abnahme. Commit „B0: Abdeckung, Backlog, Lückenprotokoll, Messung v2, Sicherheitskorrekturen, Stand-Bericht“, push, anhalten. Bericht im Format E7: (1) bestätigt (2) offen (3) Freigabe nötig – plus die Worst-Case-Zahl, das Ergebnis zu 05.01.4 und die Liste der Teamentscheidungen, die vor B1 nötig sind.
