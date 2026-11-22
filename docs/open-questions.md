# Offene Fragen

Stand: 21.11.2026.

## An die Challenge-Owner
- keine offenen Punkte (Excel-Frage unter „An die Orga“)

## An die Orga
1. Wo sind die im Abschnitt „Data“ genannten Daten: „Real-world examples of
   faulty BoQ items“, historische Projektdaten („historical project data“) und
   Einheitspreis-Kataloge („Unit price catalogs or benchmarks“)?
   Quelle: input/challenge_A_offiziell.md. [OFFEN]
2. Gibt es eine Excel-Beispieldatei? Der Challenge-Text nennt Excel als
   Importformat, der Datensatz enthält keine Excel-Datei. Bis dahin bleibt der
   Excel-Import im Prototyp ausgeschlossen. [BESTÄTIGT, Team, Chat 21.11.2026]

## An das Team
1. Zugang zu einer LLM-API für die KI-Gegenprüfung?
2. Stichwortlisten im Prüfkatalog (Nr. 5–13) abstimmen; die Trefferzahlen
   sind nicht nachgezählt.
3. Die übrigen ungeprüften Widerspruchs-Kandidaten am Original prüfen – wer?
4. Demo-Fehler für Prüfung Nr. 3 und 4: wer baut sie ein, in welche Kopie?

## Im Durchstich zu klären
- keine offenen Punkte

## Ideen (nur notiert, nicht umsetzen)
- Ausfüllfelder wie „Fabrikat: '.....'“ oder „Type: '.....'“ könnten später
  einen Hinweis „Bieterangabe erforderlich“ ergeben. Beispiel:
  Leistungsverzeichnis.pdf 5.3.100, S. 61 (docs/pruefprotokoll.md, S2).
  Der PDF-Parser lässt diese Ausfülllinien weg; ein Hinweis müsste den
  Seitentext lesen. [Team, Chat 21.11.2026]

## Erledigt
- Meilenstein What-if: Meilenstein 5 = „What-if analyses (material prices,
  alternatives)“. Quelle: input/challenge_A_offiziell.md.
  [BESTÄTIGT, Team, Chat 21.11.2026]
- Deliverables: „Demo of a web app or assistant tool with upload and risk
  report“ und „Pitch from an estimator's perspective: How does the prototype
  change the bidding process?“. Quelle: input/challenge_A_offiziell.md.
  [BESTÄTIGT, Team, Chat 21.11.2026]
- 02.05.0005 und 02.05.0009 (501-24-01_GAEB-XML_sas.x83): Der Skeptiker hat
  den Wortlaut am Original geprüft (docs/pruefprotokoll.md, Abschnitt S1);
  die DN-Werte im Langtext stehen bei Anbauteilen. Beide sind als
  Negativ-Tests in docs/acceptance.md T2 aufgenommen.
  [BESTÄTIGT, Team, Chat 20.11.2026]
- Oberflächen-Framework: Streamlit. Erste Prüfung: Nr. 1 und 2.
  KI-Anteil im Durchstich: keiner (regelbasiert). Heuristik:
  src/heuristik_widerspruch_v0.py. Eingabeumfang: 5 Testdateien, dann
  32 Dateien mit je einer Quelle. [BESTÄTIGT, Team, 20.11.2026]
  Details: docs/decisions.md.
- Dubletten: `pruefkatalog.md` (Wurzel) und `data/challenge-a/` nach
  `archiv/dubletten/` verschoben, nichts gelöscht. [BESTÄTIGT, Team, 20.11.2026]
- Fund-ID bei verschiedenen OZ-Schreibweisen und doppelter OZ: geregelt in
  docs/data-contracts.md. [BESTÄTIGT, Team, 20.11.2026]
- Abgabe LV 10.01.0001 „Material auf Nachweis zzgl. 18% GK“: steht nur in
  StBALV23040.D86 (Titel 10 „Fremdrechnungen“) und als Preiszeile in
  StBALV23040.D84; nicht in [NUMMER_001]_leer.X83 und nicht in Abgabe LV.pdf
  (endet mit Titel 9). Unterschied zwischen den Dateien, kein Parserfehler.
  [BESTÄTIGT, Team und Original, 20.11.2026]
- 139,7 mm bei 05.01.4: Außendurchmesser DN 125 (DN 100 = 114,3 mm), Quelle KSB
  (siehe docs/acceptance.md). Fund bleibt "möglicher Widerspruch".
  [BESTÄTIGT, Team, 20.11.2026] – aufgehoben durch B0b – [OFFEN – nicht belastbar bestätigt]
  (KSB-Quelle; Entscheidung 05.01.4 „echter Widerspruch“: docs/decisions.md, Zeile „B0b: Strittige
  Positionen …“; L27)
