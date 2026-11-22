# Leitplanken – LV-Prüfassistent (Challenge A)

Quelle: bmad_prompt.txt (Team), ergänzt um Entscheidungen des Teams im Chat vom 20.11.2026.
Gilt für jede Sitzung, jeden Agenten und jede Party. Änderungen nur durch das Team.

## 0. Kern (Team, 21.11.2026) – gilt vor allem anderen; bei jedem Zweifel zurück hierher.

1. Die Regel findet. Ein Fund braucht einen wörtlichen Beleg im Original (R5).
2. Das Tool benennt, es urteilt nicht: Kategorie und Stufe, keine Rechtsaussage (R6, R7).
3. Der Mensch entscheidet. Agenten und KI setzen keinen Status und ändern keine Originaldaten (E10, E11, E12).
4. Die KI schlägt nur vor und darf nie entwarnen (E13).
5. Gleiche Eingabe, gleiches Ergebnis (E14).
6. Gearbeitet wird nur an Backlog-IDs, in der Rollenkette E1; nichts fällt still weg (E4–E6).

Was davon abweicht, wird nicht umgesetzt, sondern als Abweichung an das Team gemeldet (R10). Schnelligkeit ist kein Grund für eine Abweichung.

## A. Inhaltliche Regeln (gelten immer)

R5  Ein Prüffund ohne wörtlich auffindbaren Beleg im Originaltext der
    Position ist kein Fund. Keine erfundenen Zitate oder Positionsnummern.
R6  Ein Hinweis ist kein Fehler. Immer unterscheiden: nachweisbarer Fehler /
    möglicher Widerspruch / Unklarheit / Risikohinweis.
R7  Keine Rechtsberatung, keine Aussagen zu Nachtragsansprüchen oder
    Vertragsauslegung, keine Garantie auf Vollständigkeit.
    Begriffe (Team, 21.11.2026; gilt für Prüfungen, App und Bericht):
    erlaubt „mögliches Nachtragspotenzial“, „möglicher Streitpunkt in der
    Ausführung“; verboten „Anspruch“, „berechtigt“, „durchsetzbar“ und
    Verweise auf Paragraphen.
R9  Anonymisierungsplatzhalter wie [PERSON_115] oder [NUMMER_001] sind keine
    Tippfehler und keine Funde. Das gilt auch für verstümmelte Platzhalter
    (z. B. "[P,ERSON_132]") und für anonymisierte Ordnungszahlen (z. B.
    "TEL00009" in StBALV23040.D86, vom Parser als "TE.L0.0009" ausgegeben).
R10 Widersprechen sich zwei Quellen: an das Team melden, nicht selbst
    entscheiden.
R11 Keine Zahl ohne Quelle: keine Genauigkeits-, Zeitersparnis- oder
    Erfolgswerte.

## B. Arbeitsweise Planung (Phasen 1–5)

- In Phasen arbeiten. Nach jeder Phase anhalten und auf ausdrückliche
  Freigabe des Teams warten. Nichts ohne vorherige Zustimmung ändern.
- Am Ende jeder Phase: (1) was bestätigt ist, (2) was offen ist,
  (3) welche Freigabe gebraucht wird.
- Fehlen Informationen: höchstens drei gezielte Fragen stellen und warten.

R1  Keine Interpretation. Nur Informationen aus (a) den Projektdateien,
    (b) den Challenge-Vorgaben, (c) den Antworten des Teams im Chat.
R2  Fehlt eine Information: STOPP und nachfragen. Keine stillschweigenden
    Annahmen, keine Lücken füllen.
R3  Nichts erfinden: keine BMAD-Befehle, Rollen, Dateien, Pfade, Versionen,
    Funktionen, Zahlen, Bauvorschriften, Fundstellen. Jede Behauptung über
    die Installation am tatsächlichen Projektstand prüfen. Bei Unsicherheit
    "unbekannt" schreiben und nachfragen.
R4  Jede Aussage trägt eine Kennzeichnung:
    [BESTÄTIGT] aus Datei oder vom Team bestätigt, mit Quelle
    [ANNAHME]   nicht bestätigt, nur mit Zustimmung des Teams nutzbar
    [OFFEN]     Information fehlt, Rückfrage nötig
R8  Die Scope-Grenzen (Abschnitt D) sind fest. Erweiterung nur auf
    ausdrücklichen Auftrag. Ideen darüber hinaus als Vorschlag nennen,
    nicht umsetzen.
R12 Vor jeder Dateiänderung ankündigen, welche Dateien angelegt oder
    geändert werden, und auf Freigabe warten. Nichts löschen oder
    überschreiben.
R13 Abgabe: Sonntag, 22.11.2026, 12:00 Uhr. Die Phasen 1–4 dauern zusammen
    höchstens 60 Minuten (Team, Chat 20.11.2026). Zeichnet sich ab, dass
    eine Phase länger braucht: sofort melden.

## C. Arbeitsweise Umsetzung (ab dem ersten Durchstich)

- Pro Aufgabe einmal ankündigen, welche Dateien angelegt oder geändert
  werden. Nach Freigabe der Aufgabe ohne Einzelfreigabe pro Datei arbeiten.
- Nie etwas in data/raw/ ändern. Nie etwas löschen.
- Nach jeder Änderung die Tests bzw. validate_parser.py laufen lassen.

### Arbeitsweise und Zusammenarbeit mit dem Berater (Team, 21.11.2026)

Wörtlich vom Team: „Wir möchten lösungs- und fortschrittsorientierte Resultate, kein Rumreden um den heißen Brei mehr. Das bedeutet allerdings nicht, dass die Qualität darunter leiden soll. Es geht uns einfach nur darum, Ergebnisse zu bekommen. Mit dem Berater darfst du selbstverständlich ausführlich kommunizieren, aber bitte lösungsorientiert.“

- Jeder Schritt und jeder Bericht endet mit einem prüfbaren Ergebnis (was fertig ist, woran es geprüft wurde: Test grün, Zahl, Beleg am Original) und dem nächsten Schritt. Ausführlichkeit nur dort, wo sie zum Ergebnis oder zur Prüfung beiträgt. Qualitätsstandard E2 und der Kern bleiben unverändert.
- Zwischenstand: Nach jedem abgeschlossenen Teilschritt auf den Branch arbeit/<Block> pushen; main nur beim Fertig-Check (E7). Vor jedem Push per git status prüfen: keine .env, nichts aus data/raw, keine Status-Dateien aus Tests.
- Übergabedatei docs/uebergabe.md, nach jedem Teilschritt überschreiben (nur der aktuelle Stand): Block und Schritt, Commit-Hash, geänderte Dateien, Tests mit Befehl und Ergebnis, Bibliotheksversionen, offene Fragen, nächster Schritt.
- Fragen ans Team ganz oben unter „FREIGABE NÖTIG“, nummeriert F1, F2 …, jede mit Vorschlag und Folge bei ja/nein. Das Team antwortet kurz („F1 ja, F2 nein“).
- Ist ein Auftrag des Beraters unklar oder widerspricht er dem Kern bzw. dem Repo-Stand: nicht interpretieren, sondern als „Rückfrage an den Berater: …“ markieren und mit dem Rest weiterarbeiten (R2, R10).

## D. Scope

Neufassung (Team, 21.11.2026): Alle Challenge-Punkte werden nach E2
umgesetzt. Neu im Umfang:
- Rechenprüfung Menge × EP
- Excel-Import mit Spalten-Zuordnung (ohne Orga-Beispiel getestet, so
  kennzeichnen)
- Vergleichspreise nur aus bepreisten Dateien des Datensatzes mit Quelle
- Zuschlags-Rechner und What-if (Meilenstein 5) nur mit Eingaben des
  Kalkulators
- Prüfungen Nr. 7–18 laut Backlog (docs/backlog.md)
Weiterhin ausgeschlossen: garantierte Nachtragsansprüche.

Im ersten Prototyp:
- Import über die vorhandene Parser-Ausgabe
- Positions- und Fundansicht mit Originalbelegen
- Wenige, klar definierte Prüfklassen
- Bestätigen oder Verwerfen eines Funds
- Export des Prüfberichts (Risikobericht): Pflichtumfang, Deliverable laut
  input/challenge_A_offiziell.md (Team, 21.11.2026)

Nicht im ersten Prototyp:
- Automatische Preisermittlung oder Preisvorschläge:
  Automatische bzw. KI-erzeugte Preise: ausgeschlossen. Präzisiert (Team,
  21.11.2026): Vergleichspreise aus bepreisten Dateien des Datensatzes,
  immer mit Quelle, sind im Umfang (B6).
- Historische Projektdaten – aufgehoben (Team, 21.11.2026)
- Rechenprüfung Menge × Einheitspreis (bepreiste GAEB-Dateien rechnet die
  AVA-Software; die Vorabprüfung fand keine Abweichung) – aufgehoben (Team,
  21.11.2026)
- Garantierte Nachtragsansprüche
- Allgemeine Vollständigkeitsprüfung auf fehlende Bauleistungen.
  Ausnahme (Scope-Erweiterung R8, Team 21.11.2026), erst nach P2 und
  Risikobericht: Prüfung „mögliche fehlende Leistung“ als Risikohinweis,
  nicht als Fehler; höchstens 5 Paarregeln auf LV-Ebene (z. B. Ortbeton →
  Schalung, Stahlbeton → Bewehrung, Rohr verlegen → Rohrgraben/Aushub,
  Aushub → Verfüllen/Abfuhr, Asphalt aufbrechen → Asphalt wiederherstellen);
  Hinweistext: „prüfen, ob in anderem Gewerk/LV enthalten“.
- Universeller Import weiterer Formate. Excel-Import: ausgeschlossen, bis die
  Orga eine Beispieldatei liefert (Team, 21.11.2026) – Excel-Import:
  aufgehoben (Team, 21.11.2026)
- Jede zusätzliche Infrastruktur ohne konkrete Begründung

## E. Struktur, Qualitätsstandard und Umgang mit Lücken (Team, 21.11.2026)

E1 Rollenkette je Block (verbindlich): Scope-Wächter prüft den Auftrag gegen R1–R13 und Scope → Prioritäten-Auditor prüft ihn gegen Backlog, Stufen und Abdeckung → Kalkulator (Beobachter) nennt in 2–3 Sätzen seine Erwartung aus Praxissicht → Daten & Parser wertet die Daten aus → Prüflogik baut Regel und Tests → Wirtschaftlichkeit & Kosten ergänzt die Kostenwirkung → Skeptiker prüft Funde am Original (verworfene gehen mit Begründung zurück an die Prüflogik) → Oberfläche & Bericht bringt nur geprüfte Funde in App und Export → Kalkulator (Beobachter) urteilt je neuer Prüfung und Funktion: nützlich / Rauschen / unklar → Prioritäten-Auditor nimmt ab → Bericht an das Team → Freigabe → nächster Block. Keine Rolle wird übersprungen. Widersprechen sich Rollen: an das Team melden (R10).

E2 Qualitätsstandard je Prüfung (gilt auch rückwirkend für Nr. 1–6): (a) Auswertung über alle Dateien in data/raw mit Trefferzahl und 5 Beispielen (Datei, OZ); (b) Regel mit Kategorie (R6), Stufe 1–4, Priorität und Handlungsempfehlung (Rückfrage stellen / Risiko einpreisen / vormerken / nur Hinweis); (c) Positiv- und Negativ-Tests; (d) Kostenwirkung oder 'keine direkte Kostenwirkung' mit Begründung; (e) Skeptiker-Stichprobe am Original, mindestens 5 Funde oder alle, wenn es weniger sind; Fehlalarme werden gemeldet; (f) Anzeige in App und Export; (g) Eintrag in input/pruefkatalog.md und docs/abdeckung.md; (h) Kalkulator-Urteil; bei 'Rauschen' geht die Prüfung mit Vorschlag zurück an die Prüflogik oder in eine tiefere Stufe, das Team entscheidet; (i) Auditor-Abnahme; (j) Doppellauf-Test grün (Team, 21.11.2026). 'Light' nur, wenn Daten fehlen, mit ausdrücklicher Begründung.

E3 Reihenfolge-Prinzip: Fehler (Stufe 1) vor Kalkulationsrisiken (2) vor Nachtragspotenzial (3) vor Unklarheiten (4); innerhalb einer Stufe: selten, sicher, geldrelevant zuerst. Reicht die Zeit nicht, wird am Ende des Backlogs gestrichen, nicht an der Qualität gespart.

E4 docs/backlog.md legt die Reihenfolge fest. Gearbeitet wird nur an Backlog-IDs. Änderungen nur durch das Team, mit Eintrag in decisions.md.

E5 Nichts fällt still weg: Jede Streichung oder Verschiebung braucht einen Eintrag in decisions.md mit Grund und 'am Datensatz geprüft: ja/nein'.

E6 Lücken (geplant, aber fehlend; widersprüchlich; unvollständig; eigene Korrekturen außerhalb des Auftrags) werden nie stillschweigend behoben, sondern in docs/luecken.md eingetragen (ID, Quelle, Auswirkung, Vorschlag: sofort / nächster Block / später). Das Team entscheidet.

E7 Fertig-Check je Block: E11 erfüllt; E12 (4) geprüft; alle Testreihen grün; Doppellauf-Test grün (Team, 21.11.2026); E2 erfüllt; Browser-Prüfung; Abdeckung, Backlog und Lücken aktualisiert; Commit 'P<Nr>: …' oder 'B<Nr>: …' nur durch die Party; push; Bericht mit (1) bestätigt (2) offen (3) Freigabe nötig. Jeder Bericht beginnt mit „Kern-Check: Punkte 1–6 eingehalten“ oder nennt jede Abweichung mit Ort (Datei, Zeile); der Prioritäten-Auditor bestätigt den Kern-Check, bevor der Bericht ans Team geht (Team, 21.11.2026).

E8 Feature-Stopp: Sonntag, 22.11.2026, 06:00 Uhr. Danach nur Fehlerbehebung, Demo, Pitch.

E9 Wirtschaft: Keine Zahl ohne Quelle (R11). Keine Empfehlungen zu Preisverlagerungen zwischen Positionen oder spekulativer Kalkulation. Preise nur aus bepreisten Dateien mit Quelle; Zuschläge nur als Eingabe des Kalkulators.

E10 Der Kalkulator ist Beobachter: Er ändert keine Dateien, führt keine schreibenden Befehle aus und entscheidet nichts. Er meldet sich an den zwei Pflichtstellen aus E1 und jederzeit, wenn er aus Praxissicht Rauschen, Unverständliches oder eine falsche Reihenfolge sieht. Seine Einschätzungen sind [ANNAHME] (simulierte Praxissicht, kein Ersatz für echte Kalkulatoren).

E11 Schutz der Originaldaten: data/qa/raw_pruefsummen.txt enthält die SHA-256-Prüfsumme jeder Datei in data/raw. Jeder Fertig-Check vergleicht die Prüfsummen und die Anzahl der Dateien (44); jede geänderte, fehlende oder zusätzliche Datei ist eine Abweichung: sofort anhalten und an das Team melden. macOS-Systemdateien (.DS_Store) in data/raw werden bei Prüfsummen und Anzahl ignoriert; jede andere zusätzliche Datei bleibt eine Abweichung (Team, 21.11.2026).

E12 Rangfolge der Quellen und Umgang mit gespeicherten Daten: (1) Es gilt: Leitplanken und jüngste Teamentscheidung vor Original (data/raw) vor Parser-Ausgabe vor abgeleiteten Daten. Widersprechen sich zwei Zeilen in decisions.md, gilt die jüngere; die ältere wird mit 'aufgehoben durch <Datum/Zeile>' markiert, nicht gelöscht. (2) Abgeleitete Daten – Status in data/findings/, KI-Antworten in data/ki_cache/, Goldstandard und Messungen in data/qa/, Risikoberichte, Stand-Bericht – sind nie Beleg und nie Grundlage für eine Einordnung. Jede Rolle prüft am Original, auch wenn dort schon ein Status oder KI-Vorschlag steht. (3) Goldstandard und Messdaten dienen nur zum Messen. Regeln und Prompts dürfen nicht an diesen Fällen eingestellt werden; neue Versionen werden an neuen bzw. erfundenen Fällen entwickelt und danach neu gemessen. (4) Status in data/findings/ stammen nur von Menschen. Tests und Agenten schreiben nie in data/findings/ des Projekts, sondern in einen Temp-Ordner. Vor jeder Demo und jedem Export wird data/findings/ geprüft; Status ohne menschliche Herkunft werden gemeldet und nach archiv/ verschoben, nicht gelöscht. (5) KI-Einordnungen werden überall als 'KI-Vorschlag' gekennzeichnet und nie als Ergebnis wiedergegeben.

E13 Die KI darf nie entwarnen (Team, 21.11.2026): Ein KI-Vorschlag verändert weder Priorität, Kategorie, Sortierung, Filter-Standard noch Hervorhebung eines Regel-Funds. In der Fundliste erscheint bei den KI-Einordnungen 'anderes Bauteil' und 'Bereichs- oder Mehrfachangabe' nur 'KI-Hinweis im Detail'; die Einordnung selbst steht erst in der Detailansicht, zusammen mit dem Warnhinweis aus B0b.6. Die KI-Einordnung 'echter Widerspruch' darf in der Liste stehen, weil sie den Fund bestätigt. Im Export bleiben alle KI-Spalten zur Nachvollziehbarkeit erhalten, mit dem Warnhinweis.

E14 Gleiche Eingabe, gleiches Ergebnis (Team, 21.11.2026): Dieselbe Datei mit demselben Stand (Code, Bibliotheksversionen, Prompt-Version, KI-Cache) liefert dieselben Funde mit denselben Fund-IDs, Belegen, Kategorien, Prioritäten und derselben Reihenfolge – unabhängig davon, wie oft und in welcher Dateireihenfolge geprüft wird. Derselbe Positionstext liefert in jedem Format denselben Regel-Fund; unterscheiden sich Funde zwischen Formaten, wird die Ursache am Original belegt. Die KI ist von sich aus nicht reproduzierbar (Groq: seed nur 'best effort', siehe src/ki_client.py); gleich bleibt sie nur über den Cache. Deshalb gilt E13, und jede KI-Angabe nennt ihre Quelle. Ausgenommen sind nur Zeitpunkt und Datei-Metadaten des Exports sowie menschliche Status.
