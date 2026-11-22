# Datenverträge

Stand: 20.11.2026.

## LV-Position

Maßgeblich ist die Ausgabe von `parse()` aus `src/lv_parser.py`
(pandas DataFrame, eine Zeile pro Titel oder Position, Spaltenliste `COLUMNS`).
`data/parsed/alle_LVs_geparst.xlsx` ist nur eine abgeleitete Ansicht
(Spalte `projekt` statt `format`/`typ`, nur Positionen, je LV eine Quelle)
und kein Vertrag. [BESTÄTIGT, Team, Chat 20.11.2026]

| Spalte | Inhalt | Quelle im Code / Beobachtung |
|---|---|---|
| `datei` | Dateiname ohne Pfad | `Path(path).name` |
| `format` | `GAEB XML`, `GAEB 90` oder `PDF` | `detect_format()` |
| `seite` | Seitenzahl, nur bei PDF; bei GAEB leer | Phase 1: leer in allen GAEB-Zeilen |
| `typ` | `Titel` oder `Position` | `make_row(typ=…)` |
| `oz` | Ordnungszahl, wie in der Datei geschrieben (z. B. `05.01.4`, `3.1.180`, `10.01.0001`). Auch ungewöhnliche Schreibweisen bleiben, z. B. `.48` in LV_14b_Dachentwaesserung.pdf (alle 60 OZ mit führendem Punkt, steht so im Original). Die App zeigt die Original-OZ; die normalisierte OZ steht nur in der Fund-ID. [BESTÄTIGT, Team, Chat 20.11.2026] | GAEB 90: `clean_oz()` |
| `titel` | Titeltext | – |
| `kurztext` | Kurztext; bei PDF die erste Textzeile der Position (nicht ausgezeichnet) | bekannte Grenze, bmad_prompt.txt |
| `langtext` | Langtext | – |
| `menge` | Zahl oder leer | `de_number()` |
| `einheit` | normalisierte Einheit (z. B. `m²`, `m³`, `St`, `psch`, `h`). Keine Einheit steht als `None` oder `""`; beide bedeuten „keine Einheit“, im Code mit `not einheit` prüfen. Der Parser bleibt unverändert. [BESTÄTIGT, Team, Chat 20.11.2026] | `UNIT_MAP`, `norm_unit()`; D1 20.11.2026: 249 × `None`, 38 × `""` in 43 Dateien |
| `einheit_roh` | Einheit wie im Original | – |
| `ep` | Einheitspreis oder leer | – |
| `gp` | Gesamtpreis oder leer | – |
| `art` | `Normal` oder kommagetrennt aus `Bedarf`, `Wahl`, `Zulage`, `Pauschal`, `Stundenlohn`, `Verweis` | `art_from()`; teils aus Text und Einheit abgeleitet |
| `art_roh` | Vermerke aus dem Original, z. B. „Bedarfsposition …“, „Wahlposition/ALN …“, „enthält Bild/Skizze“ | GAEB XML: Vermerke; GAEB 90: Kennzeichen aus Spalte 12–14 (z. B. `NNN`, `NNL`); PDF: Vermerk aus dem Text (z. B. „Bedarfsposition ohne GB“) [BESTÄTIGT, Team, Chat 20.11.2026; D1 20.11.2026] |

Wiederholbarkeit: `fingerprint(df)` (SHA-256 über die CSV-Form, 16 Zeichen)
muss für dieselbe Datei immer gleich sein.

## Prüffund

Speicherformat: JSON. [BESTÄTIGT, Team, Chat 20.11.2026]

| Feld | Typ | Inhalt |
|---|---|---|
| `id` | String | `"<Prüfkatalog-Nr>\|<datei>\|<oz normalisiert>"`, deterministisch, z. B. `"1\|8209.003_Leistungsverzeichnis_leer.X83\|5.1.4"` (siehe Regeln unten) |
| `pruefung` | Zahl | Nr. aus input/pruefkatalog.md |
| `kategorie` | String | genau einer von: `nachweisbarer Fehler`, `möglicher Widerspruch`, `Unklarheit`, `Risikohinweis` (R6) |
| `titel` | String | kurze Bezeichnung des Funds |
| `positionen` | Liste | je Eintrag `{datei, oz, seite}` mit Original-OZ; `seite` null bei GAEB |
| `belege` | Liste von Strings | wörtliche Zitate aus `kurztext`/`langtext` der Position (R5); bei PDF auch der Vermerk aus `art_roh` (z. B. „Bedarfsposition ohne GB“ aus der Zeile „*** …“) |
| `feldbelege` | Liste, optional (fehlt = keine) | Belege, die kein Zitat sind, je `{art, text}`; `art` = `Feldwert` (z. B. `Einheit: (leer)`, `Menge: 0`, `Einheit: psch`) oder `Kennzeichen in der Datei` (z. B. `<Provis>WithoutTotal</Provis>` bei GAEB XML). Die App zeigt sie getrennt von den Zitaten. [BESTÄTIGT, Team, Chat 21.11.2026] |
| `begruendung` | String | warum der Beleg den Fund trägt |
| `stufe` | Zahl 1–4 | Art des Funds nach E3: 1 Fehler, 2 Kalkulationsrisiko, 3 Nachtragspotenzial, 4 Unklarheit (F1, Team 21.11.2026). Anzeige in App und Export: „1 – Fehlerprüfung“, „2 – Kalkulationsrisiko“, „3 – mögliches Nachtragspotenzial“, „4 – Unklarheit“ (F4, Team 21.11.2026, B1b). „Menge 0“ (Nr. 3): Stufe 2 (F2, B1b). Bis B0b hieß das Feld `prioritaet`; Werte unverändert übernommen (B0b.4) |
| `stufe_begruendung` | String | Quelle der Stufe (Prüfkatalog oder Teamentscheidung); bis B0b `prioritaet_begruendung` |
| `prioritaet_in_stufe` | Zahl ≥ 1 | Rang der Prüfung innerhalb ihrer Stufe nach E3 („selten, sicher, geldrelevant“ gemeinsam abgewogen; 1 = zuerst), fest je Prüfung (`PRIORITAET_IN_STUFE` in src/pruefung_widerspruch.py, input/pruefkatalog.md). App und Export zeigen ihn als „Rang in Stufe“ (F4, B1b; bis B1a „Priorität“). Sortierung: `stufe`, dann `prioritaet_in_stufe`, dann OZ (F1) |
| `rueckfrage` | String oder null | optionale klärende Rückfrage an den Auftraggeber (keine Rechtsaussage, R7) |
| `status` | String | `offen`, `bestätigt`, `verworfen` oder `Rückfrage stellen` (letzteres seit P3b, Team 21.11.2026; im Export als „Entscheidung Kalkulator“ vorausgefüllt) |

### Nr. 1: Mehrfachangaben „DN a/b“ (B1q, Team 21.11.2026)

„DN a/b“ ist eine DN-Angabe mit mehreren Werten (`dn_angaben()` in src/pruefung_widerspruch.py); die
Begründung nennt sie als „DN 125/100“. Folgt dem zweiten Wert eine Länge („… mm lg“, „lang“, „Länge“,
„Baulänge“), ist er keine Nennweite. Sonst gleiche Begründung wie bisher.

### B2-Integration (21.11.2026)

- `alle_pruefungen(df, quelle)` liefert Nr. 1–19; bei PDF und GAEB 90 ist `quelle` Pflicht (Belege am Original).
- `format` kann zusätzlich „Excel“ sein (src/excel_import.py; `seite` und `art_roh` leer).
- `bericht.pruefe_lv(pfad, zuordnung=None)`: Excel-Weiche; `info` zusätzlich `kurztexte`, `gp`, `einheiten` je OZ
  (Übersichtsseite, Vergleichspreise).
- App-Sitzung: `st.session_state["lv_uebersicht"]` und `["lv_downloads"]` für src/pages/0_Uebersicht.py.

### Nr. 17 Rechenprüfung (B1e, Team 21.11.2026)

Fund-ID `17|<datei>|<oz>`; `belege` = Kurztext (leer in reinen Preisdateien), `feldbelege` = `Menge: 3,000 m`,
`EP: 1.200,00`, `GP: 3.800,00` (Art „Feldwert“). Prüfabdeckung: Eintrag mit `pruefung` 17 und `text`
„Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“. Spalte „Prüfer“ im Export aus `bericht.PRUEFER`.

### PDF: Kurz- und Langtext (B1p, Team 21.11.2026, F3)

Im PDF-Zweig von `parse()` stammen `kurztext` und `langtext` nur aus dem Text der Position: Kopf- und
Fußzeilen (auch kurzer PDFs mit 2–3 Seiten), „Zusammenstellung …“, „Zuzüglich der gesetzlichen
Mehrwertsteuer …“ und der Schluss des LV gehören nicht dazu. Umbrochene Kurztext-Zeilen (gleiche Schrift wie
der Kurztext, andere als der Langtext) gehören zum `kurztext`. Angebots-Ausdrucke mit Menge in der OZ-Zeile
drucken nur den Kurztext: dort ist `langtext` = `kurztext`. Bekannte Grenzen: docs/luecken.md L45.

### Positionsgrenze und Unterbeschreibungen (B1p3, Team 22.11.2026, F1/F2)

PDF: Hinter der letzten Mengenzeile eines Blocks gehört nur eine Unterbeschreibung zur Position. Sie beginnt mit der Zeile „Unterbeschreibung N:“ (selbst nicht im `langtext`) und endet an „Gemäß … N:“, „Leitbeschreibung:“, „*** …“, der nächsten OZ oder dem Schlussteil. Aller andere Text dort (Hinweistexte, Spezifikationen, Vorbemerkungen, Abschnittstitel) gehört zu keiner Position. GAEB XML: `langtext` = `DetailTxt` + je `SubDescr` Kurz- und Langtext. Eine OZ mit leerer Ebene („1.2..2“) bleibt wie gedruckt. Mengenzeilen ohne Einheit ergeben `einheit` = ""; „pau“ wird zu `psch`, `einheit_roh` bleibt wie gedruckt.

### Prüfabdeckung je Datei (B1b, Nachtrag 3; Team 21.11.2026)

`bericht.pruefe_lv()` liefert in `info["abdeckung"]` je Prüfung Nr. 1–6 einen Eintrag
`{pruefung, name, pruefbar, gesamt, gruende}` (src/pruefabdeckung.py); `gruende` = Liste `(Grund, Anzahl)`.
App-Kopf und Blatt „Übersicht“ zeigen ihn als „prüfbar in N von M Positionen; übrige …“. Ein Hinweis:
die Prüfungen laufen unverändert über alle Positionen, kein Fund wird unterdrückt. Regeln: Nr. 1/2 brauchen
Kurztext und eigenen Langtext (`eigener_langtext`), Nr. 3, 5, 6 einen Kurztext, Nr. 4 die OZ. Reine
Preisdateien: leere Liste. B1d und B1e hängen eigene Einträge an.

### Regeln für die Fund-ID [BESTÄTIGT, Team, Chat 20.11.2026]
- In der ID steht die normalisierte OZ: führende Nullen je Abschnitt
  entfernen, wie `key()` in `src/validate_parser.py`
  (`"01.01.0001"` → `"1.1.1"`, `"05.01.4"` → `"5.1.4"`).
- In `positionen` und in den Belegen bleibt die Original-OZ.
- Höchstens ein Fund je Prüfung, Datei und normalisierter OZ. Mehrere Belege
  stehen im selben Fund.
- Eine doppelte OZ (Prüfung Nr. 4) ist ein Fund mit mehreren betroffenen
  Positionen in `positionen`.

Beispiel – tatsächliche Ausgabe von `alle_pruefungen()` (Stand B1a, 21.11.2026; L21). Beide Belege
vom Skeptiker wörtlich im Original 8209.003_Leistungsverzeichnis_leer.X83 gefunden (Textsuche,
„Druckrohr“ steht dort im nächsten Absatz). „139,7 x 2,6 mm“ steht ebenfalls im Langtext, ist aber kein
Beleg des Funds: Nr. 1 zitiert nur den Ausschnitt um den DN-Wert (5 Wörter davor und danach).

```json
{
  "id": "1|8209.003_Leistungsverzeichnis_leer.X83|5.1.4",
  "pruefung": 1,
  "kategorie": "möglicher Widerspruch",
  "titel": "Nennweite (DN) im Kurztext ≠ Langtext",
  "positionen": [{"datei": "8209.003_Leistungsverzeichnis_leer.X83", "oz": "05.01.4", "seite": null}],
  "belege": ["Edelstahl-Rohr DN 125", "Edelstahlrohr DN 100, bis PN 16 Druckrohr"],
  "begruendung": "Kurztext nennt DN 125, Langtext nennt DN 100; kein Wert stimmt überein.",
  "stufe": 1,
  "stufe_begruendung": "Stufe 1 laut input/pruefkatalog.md, Nr. 1",
  "prioritaet_in_stufe": 4,
  "rueckfrage": null,
  "status": "offen"
}
```


## KI-Vorschlag (P4)

Getrennt vom Fund, je Fund-ID, nur für Prüfungen Nr. 1 und 2. Der Regel-Fund wird nie
verändert. Quelle: `src/ki_pruefung.py`. [BESTÄTIGT, Team, Chat 21.11.2026]

Antwort der KI (JSON-Text, vom Code geprüft):

| Feld | Inhalt |
|---|---|
| `einordnung` | genau eine von `echter Widerspruch`, `anderes Bauteil`, `Bereichs- oder Mehrfachangabe`, `unklar` |
| `begruendung` | höchstens 2 Sätze |
| `zitat_kurztext`, `zitat_langtext` | wörtlich aus Kurz- bzw. Langtext (Leerraum zusammengefasst) |
| `rueckfrage` | Entwurf einer Bieterfrage, nur bei `echter Widerspruch` oder `unklar`, sonst leer |

Ergebnis je Fund (App und Export): `status` (`KI-Vorschlag gültig`, `KI-Antwort unlesbar`,
`KI-Vorschlag verworfen: Zitat nicht im Original`, `KI-Vorschlag verworfen: R7`,
`KI-Antwort abgelehnt`), die Felder oben (nur bei gültigem Vorschlag gefüllt),
`zitat_status`, `anbieter` (`groq` oder `anthropic`), `modell` (antwortendes Modell), `prompt_version`, `quelle` (`Cache` oder `API`).

Cache: `data/ki_cache/<sha256>.json`, Schlüssel aus Anbieter, Modell, Denkaufwand, Prompt-Version,
Systemprompt und Positionstext. Log: `data/qa/ki_log.jsonl`, je Aufruf Zeit, Fund-ID, Anbieter, Modell, Versuch,
stop_reason, usage, Dauer, Wartezeit, geschätzte Kosten (nur Anthropic), Ergebnis; technische
Fehler mit `usage: null`; nie Key oder Positionstext.

Goldstandard `data/qa/ki_goldstandard.json`, je Eintrag: `fund_id`, `einordnung` (eine der vier
Einordnungen, `offen` oder `strittig`), `zaehlt`, `quelle`, `regel_fund` (false bei den
Zusatzfällen, die der DN-Filter aussortiert). Strittig (Team, 21.11.2026): bisheriger Eintrag
bleibt und trägt `strittig`, `einordnung_person_b`, `quelle_person_b`; die übrigen Einträge der
Position tragen `einordnung: strittig`, `zaehlt: false` und `einordnungen` (beide mit Quelle).
Strittige Einträge stehen in der Messung getrennt und zählen nicht in der Trefferquote.
