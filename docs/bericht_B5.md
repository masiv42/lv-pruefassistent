# Bericht B5 – KI: Tippfehler, Widerspruch zwischen Positionen (Sitzung B1)

Stand: 21.11.2026, Branch arbeit/B5. Rollenkette vor dem Code: docs/uebergabe.md (Abschnitt B5).

**Kern-Check:** Punkte 1–6 eingehalten.
- Die KI macht nur Vorschläge. Sie stehen in der App getrennt von den Regel-Funden und ändern keinen Fund, keine
  Sortierung und keinen Filter (Kern 4, E13).
- Die Zitate prüft der Code wörtlich am Text der Position (R5). Platzhalter verwirft er (R9), R7-Begriffe ebenfalls.
- Bei gleichem Cache-Stand liefert ein Lauf dasselbe Ergebnis (E14). Die Messfälle wurden nicht an die Antworten
  angepasst (E12 (3)).

## Ergebnis

- **src/ki_b5.py:**
  - Prompts B5-T1 (Tippfehler) und B5-W1 (Widerspruch zwischen Positionen), wörtlich aus docs/b5_prompt_entwurf.md
    und per SHA-256 eingefroren.
  - Antwort-Schema je Prüfung (Groq `json_schema`, strict).
  - Prüfkette: Schema, R7, wörtliches Zitat in der richtigen Position, R9.
  - Cache data/ki_cache, Log data/qa/ki_log.jsonl.
  - Höchstens 50 Aufrufe je Klick; der nächste Klick macht weiter.
- **Vorauswahl der Paare als Regel:**
  - Bedingungen: gleicher Abschnitt (OZ ohne letzte Stelle), ein gemeinsames Wort ab 4 Buchstaben im Kurztext,
    verschiedene DN-Werte oder Betonklassen.
  - Höchstens 50 Paare, feste Reihenfolge.
- **App:**
  - Neuer Aufklapper „KI-Prüfungen (B5) … nur KI-Vorschlag“ mit je einem Knopf.
  - Angezeigt werden „N von M geprüft, K KI-Vorschläge“ und je Vorschlag Zitat, Korrektur bzw. Rückfrage-Entwurf,
    Kategorie und Stufe als Vorschlag, Quelle (API/Cache) und Modell.
  - Ohne Klick liest die App nur den Cache und ruft nichts auf.
- **ki_client:** `anfrage(…, schema=None)`. Groq nutzt das übergebene Schema; Anthropic nimmt es an und folgt dem
  System-Prompt.

## Messung an den 32 erfundenen Fällen (Sitzung B2)

Groq openai/gpt-oss-120b, 32 Aufrufe, data/qa/b5_messung.json (Stand 23:12). Es sind Anzahlen erfundener Fälle,
keine Treffsicherheit am Datensatz (R11).

| Prüfung | Fälle | richtig | nicht richtig |
|---|---|---|---|
| Tippfehler, positiv | 8 | 8 | – |
| Tippfehler, negativ | 8 | 6 | T-01, T-02: KI nennt die Einheit „psch“ als Tippfehler; der Code verwirft das (das Zitat steht nicht im Kurz- oder Langtext) → **kein falscher Vorschlag sichtbar** |
| Widerspruch, positiv | 8 | 5 | W+03, W+05: KI zitiert die Mengenzeile („Menge: 120 m“), die nicht im Positionstext steht → verworfen, also verpasst. W+08 (W2.1-E gegen W1-E): KI „gewollt verschieden“ → verpasst |
| Widerspruch, negativ | 8 | 8 | – |

**Kein falscher Vorschlag erreicht die Person.** Es gibt aber 3 verpasste Widersprüche (W+03, W+05, W+08). Weil die
KI nie entwarnt (E13), ändert das an den Regel-Funden nichts.

## Tests

- src/test_ki_b5.py: 16/16 mit Ersatz-Client, ohne API-Aufruf. Geprüft werden:
  - Einfrierung der Prompts, R5, R9, R7, unlesbare Antwort, Zitat in der falschen Position
  - Schema-Übergabe, E13, Cache (zweiter Lauf ohne Aufruf), Obergrenze, KI aus
  - Paar-Regel und Messung
- test_ki_client 33/33 und test_ki_pruefung 54/54 sind unverändert grün.
- Alle Testreihen grün; Doppellauf 13/13; Durchlauf 43 OK, 1 HINWEIS, 0 FEHLER; E11 44/44.

## Grenzen (docs/luecken.md)

- Die Paar-Vorauswahl vergleicht nur Positionen, keine Vorbemerkung mit einer Position. Der Prompt erlaubt
  beides; Vorbemerkungen hat der Datensatz nur teilweise als Text.
- Mengenzeile als Beleg (W+03, W+05): Vorschlag F3.
- Die B5-Vorschläge stehen noch nicht im Risikobericht, nur in der App.

## Kalkulator-Urteil [ANNAHME]

**Nützlich, mit Vorbehalt.** Tippfehler als Hinweis sind brauchbar. Gut ist, dass die falsche „psch“-Meldung nicht
durchkommt. Bei Widersprüchen fehlen 3 von 8. Das ist kein Schaden, solange die Regel-Funde bleiben, aber ich
verlasse mich nicht darauf.

## Prioritäten-Auditor

Abgenommen. Kern-Check bestätigt. Offen ist F3 (Mengenzeile als Beleg); sie blockiert nicht. Jede Änderung an
Prompt oder Prüfkette braucht eine neue Version und neue, erfundene Fälle (E12 (3)).
