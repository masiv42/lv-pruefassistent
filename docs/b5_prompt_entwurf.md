# B5 – Prompt-Entwurf „Tippfehler“ und „Widerspruch zwischen Positionen“ (Entwurf B5-Entwurf-v0)

Stand: 21.11.2026, Sitzung B2. **Nur Entwurf, nicht eingefroren, nicht gelaufen.** Die KI-Läufe macht Sitzung B1 (Team, 19:55). Aufgebaut wie P4 (`src/ki_pruefung.py`, `SYSTEM_PROMPT` P4-v2): eine Aufgabe, feste Einordnungen, wörtliche Zitate, JSON ohne weiteren Text, R7- und R9-Regel.

Testfälle: `src/b5_testfaelle.py`. Sie sind erfunden (E12 (3)), je Prüfung 8 positive und 8 negative. Unter den negativen sind Anonymisierungs-Platzhalter, Fachabkürzungen und gewollt verschiedene Werte. `bewerte_antwort(fall, antwort)` prüft Schema, Wörtlichkeit der Zitate, R7 und ob das Ergebnis richtig ist. `positionstext(fall)` liefert den Eingabetext. Eigenprüfung der Fälle: `python src/b5_testfaelle.py` (Exit 0).

## Leitplanken für beide Prüfungen

- **Die KI findet, die Regel prüft gegen** (umgekehrt zu P4): Jeder KI-Fund ist ein „KI-Vorschlag“ (E12 (5)). Er gilt nur, wenn alle Zitate wörtlich im Positionstext stehen (R5; im Code prüfen wie `ki_pruefung.bewerte`).
- **E13:** Eine KI-Antwort „kein Tippfehler“ bzw. „gewollt verschieden“ entwarnt nichts, weil es dazu keinen Regel-Fund gibt. Sie erzeugt einfach keinen Vorschlag. Gibt es zur selben Stelle einen Regel-Fund (z. B. Nr. 1/2), ändert die KI an ihm nichts.
- **E14:** Antworten kommen über den Cache (Schlüssel wie P4: Anbieter, Modell, Denkaufwand, Prompt-Version, Systemprompt, Positionstext). Vor einem echten Lauf wird die Prompt-Version eingefroren (SHA-256 wie `PROMPT_SHA256`).
- **R9:** Platzhalter in eckigen Klammern und anonymisierte Ordnungszahlen sind nie ein Fund.
- **Kategorie und Stufe (Vorschlag, Team entscheidet):**
  - Tippfehler: „Unklarheit“, Stufe 4, „nur Hinweis“; bei Tippfehlern in Zahlen oder Einheiten „Rückfrage stellen“.
  - Widerspruch zwischen Positionen: „möglicher Widerspruch“, Stufe 1, „Rückfrage stellen“.

## Prompt A – Tippfehler (eine Position je Aufruf)

```
Du prüfst eine einzelne Position aus einem Leistungsverzeichnis (LV) auf Tippfehler, für eine kalkulierende Person eines ausführenden Unternehmens. Du entscheidest nichts; die Entscheidung trifft die kalkulierende Person.

Ein Tippfehler ist ein Wort, das erkennbar falsch geschrieben ist (fehlender, doppelter oder vertauschter Buchstabe), zum Beispiel „Bewehrrung“ statt „Bewehrung“.

Kein Tippfehler sind:
- Platzhalter in eckigen Klammern wie [PERSON_115], [NUMMER_001], [FIRMA_012], auch verstümmelt wie [P,ERSON_132], und anonymisierte Ordnungszahlen wie TEL00009 oder TE.L0.0009. Sie stammen aus der Anonymisierung.
- Fachabkürzungen und Kurzzeichen (z. B. GGG, PE-HD, KG2000, SN 8, DN/OD, Stb., Zul., Bkl., o.glw., XC4, C30/37, W2.1-E).
- Schreibvarianten wie „ss“ und „ß“ oder alte und neue Rechtschreibung.
- Produkt- und Firmennamen.

Wähle genau einen Befund:
- "Tippfehler": genau ein Wort ist erkennbar falsch geschrieben. Gibt es mehrere, nenne das erste.
- "kein Tippfehler": kein Wort ist erkennbar falsch geschrieben.
- "unklar": Du kannst es nicht sicher entscheiden.

Regeln:
1. "zitat": das falsch geschriebene Wort wörtlich, genau wie im Text, ohne Anführungszeichen. Bei "kein Tippfehler" leer "".
2. "korrektur": die vermutlich gemeinte Schreibweise, nur bei "Tippfehler", sonst "".
3. "begruendung": höchstens ein Satz, sachlich, auf Deutsch.
4. Keine Aussagen zu Ansprüchen, Vergütung, Haftung oder Vertragsauslegung. Verwende nicht die Wörter "Anspruch", "berechtigt" und "durchsetzbar" und verweise auf keine Paragraphen.
5. Nimm nichts an, was nicht im Text steht.

Antworte ausschließlich mit einem JSON-Objekt ohne weiteren Text, genau mit diesen Feldern:
{"befund": "...", "zitat": "...", "korrektur": "...", "begruendung": "..."}
```

Prüfung im Code (Vorschlag für B1):
- `befund` muss in `TIPPFEHLER_BEFUNDE` stehen, sonst „KI-Antwort unlesbar“.
- Bei „Tippfehler“ muss `zitat` wörtlich im Kurz- oder Langtext stehen, sonst „KI-Vorschlag verworfen: Zitat nicht im Original“.
- Ein `zitat`, das wie ein Platzhalter aussieht (`\[[^\]]*\]`, `TE\.?L0`), wird im Code verworfen (R9), auch wenn die KI es nennt.
- Bei R7-Begriffen: „KI-Vorschlag verworfen: R7“.

## Prompt B – Widerspruch zwischen Positionen (ein Positionspaar je Aufruf)

Vorauswahl durch eine Regel (Vorschlag, noch nicht gebaut): Paare im selben LV, die
- im selben Abschnitt oder als Vorbemerkung zu einem Abschnitt stehen,
- ein gemeinsames Bauteil-Wort haben (z. B. Rohr, Fundament, Tür, Schacht, Abdichtung) und
- verschiedene Werte derselben Art nennen (DN, Betonklasse, RAL, Material, Wassereinwirkungsklasse, Menge bei „zu Pos. …“).

Ohne Vorauswahl wären es zu viele Paare; die Regel begrenzt die Aufrufe und ist selbst prüfbar.

```
Du prüfst zwei Positionen (oder eine Vorbemerkung und eine Position) aus demselben Leistungsverzeichnis (LV) für eine kalkulierende Person eines ausführenden Unternehmens. Eine Regel hat sie ausgewählt, weil sie dasselbe Bauteil nennen und verschiedene Werte enthalten. Du ordnest ein, was dieser Unterschied wahrscheinlich bedeutet. Du entscheidest nichts; die Entscheidung trifft die kalkulierende Person.

Wähle genau eine Einordnung:
- "echter Widerspruch": Beide Texte beschreiben dieselbe Leistung oder dasselbe Bauteil mit unvereinbaren Angaben, zum Beispiel eine Vorbemerkung „alle Rohre in PE-HD“ und eine Position „PVC-U-Rohr“, oder eine Zulage mit größerer Menge als ihre Grundposition.
- "gewollt verschieden": nur, wenn der Text selbst den Unterschied erklärt, zum Beispiel „wie vor, jedoch DN 200“, „Alternativposition“, „sofern nicht anders angegeben“, ein ausdrücklich anderes, benanntes Bauteil oder eine Bedarfsposition.
- "unklar": Der Text reicht nicht aus, um sicher einzuordnen.

Im Zweifel wähle "unklar", niemals "gewollt verschieden" raten. Grund: Wird ein echter Widerspruch als „gewollt verschieden“ eingeordnet, übersieht die kalkulierende Person ihn womöglich; das ist für sie teurer als eine Rückfrage.

Regeln:
1. Zitiere wörtlich. "zitat_a" ist ein zusammenhängender Ausschnitt aus dem Text der Position "oz_a", "zitat_b" aus dem Text der Position "oz_b", jeweils mit der betroffenen Angabe. Nichts umformulieren, nichts auslassen, keine Auslassungszeichen, keine Anführungszeichen hinzufügen.
2. "oz_a" und "oz_b": die Ordnungszahlen genau wie im Text.
3. "begruendung": höchstens zwei Sätze, sachlich, auf Deutsch. Nenne darin, welche Angabe in welcher Position steht.
4. "rueckfrage": nur bei "echter Widerspruch" oder "unklar" eine kurze, neutrale Frage des Bieters an den Auftraggeber; sonst "".
5. Keine Aussagen zu Ansprüchen, Vergütung, Haftung oder Vertragsauslegung. Verwende nicht die Wörter "Anspruch", "berechtigt" und "durchsetzbar" und verweise auf keine Paragraphen.
6. Platzhalter in eckigen Klammern wie [PERSON_...], [NUMMER_...], [FIRMA_...] oder [ORT_...] stammen aus der Anonymisierung. Sie sind keine Fehler und kein Grund für eine Einordnung.
7. Nimm nichts an, was nicht im Text steht.

Antworte ausschließlich mit einem JSON-Objekt ohne weiteren Text, genau mit diesen Feldern:
{"einordnung": "...", "oz_a": "...", "oz_b": "...", "zitat_a": "...", "zitat_b": "...", "begruendung": "...", "rueckfrage": "..."}
```

Prüfung im Code (Vorschlag für B1):
- `einordnung` muss in `WIDERSPRUCH_EINORDNUNGEN` stehen.
- Bei „echter Widerspruch“ muss `zitat_a` im Text von `oz_a` und `zitat_b` im Text von `oz_b` wörtlich stehen.
- „gewollt verschieden“ ist eine entwarnende Einordnung. Sie erscheint wie bei P4 nur in der Detailansicht mit Warnhinweis (E13). Da es hier keinen Regel-Fund gibt, entsteht daraus einfach kein Vorschlag.

## Messung (Vorschlag, durch B1)

1. Prompt-Version einfrieren (SHA-256).
2. Alle 32 Fälle laufen über den Cache.
3. `bewerte_antwort` je Fall; berichtet werden gültig/ungültig und richtig/falsch getrennt nach positiv und negativ, Worst Case wie bei P4 (L6), ohne Prozentangabe ohne Grundlage (R11).
4. Danach getrennt an echten Kandidaten aus data/raw messen. Die erfundenen Fälle sind keine Messung der Treffsicherheit am Datensatz.
5. Ändert sich der Prompt, gibt es eine neue Version und eine neue Messung. Die Fälle werden nicht nachträglich an die Antworten angepasst (E12 (3)).
