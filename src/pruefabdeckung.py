"""
pruefabdeckung.py - Prüfabdeckung je Datei (B1b, Nachtrag 3; Team 21.11.2026).

Gemeinsamer Baustein für App-Kopf und Risikobericht (Blatt „Übersicht“); B1d und B1e hängen eigene
Einträge an. Je Prüfung: „prüfbar in N von M Positionen“ und der Grund für die übrigen. Ein Hinweis,
der keinen Fund unterdrückt: die Prüfungen laufen unverändert über alle Positionen; hier wird nur
gezählt, in wie vielen Positionen eine Prüfung überhaupt etwas finden kann.

Regeln (gleich wie in den Prüfungen, nicht neu erfunden):
- Nr. 1/2 brauchen einen Kurztext und einen eigenen Langtext (pruefung_widerspruch.eigener_langtext).
- Nr. 3, 5, 6 brauchen einen Kurztext als wörtlichen Beleg (R5, pruefung_formal.pruefe_formal).
- Nr. 4 prüft die OZ aller Positionen.
- Nr. 17 Rechenprüfung (B1e): „Rechenprüfung: N Positionen nachgerechnet, K Abweichungen“, auch bei 0; als einziger
  Eintrag auch bei reinen Preisdateien (sonst wird dort nichts geprüft).
"""
from pruefung_formal import nur_preise, _txt
from pruefung_rechnung import abdeckung_eintrag as rechnung_eintrag
from pruefung_widerspruch import eigener_langtext, normalisiere_leerzeichen

NAMEN = {1: "Nennweite (DN) im Kurztext ≠ Langtext", 2: "Betonfestigkeitsklasse im Kurztext ≠ Langtext",
         3: "Menge oder Einheit fehlt", 4: "OZ doppelt im selben LV", 5: "Bedarfsposition", 6: "Pauschale",
         7: "Produktvorgabe „oder gleichwertig“", 8: "Bestand, vorhandene Anlagen", 9: "Entsorgung, Boden",
         10: "Vorhalten, bauzeitabhängig", 11: "Vage Formulierung", 12: "Verweistext („wie vor, jedoch“)",
         13: "Stundenlohnarbeiten", 14: "Position enthält Bild/Skizze", 15: "Zulage ohne erkennbare Grundposition",
         16: "Gleiche Leistung zweimal im selben Abschnitt", 18: "Ungewöhnliche Mengen (Menge 1 bei Mengeneinheit)",
         19: "Mögliche fehlende Leistung"}
OHNE_KURZTEXT = "ohne Kurztext"
OHNE_LANGTEXT = "ohne eigenen Langtext (Langtext leer oder gleich dem Kurztext)"


def _eintrag(nr, pruefbar, gesamt, gruende):
    return {"pruefung": nr, "name": NAMEN[nr], "pruefbar": pruefbar, "gesamt": gesamt,
            "gruende": [(g, n) for g, n in gruende if n]}


def abdeckung(df):
    """Liste von Einträgen {pruefung, name, pruefbar, gesamt, gruende=[(Grund, Anzahl)]}, Reihenfolge Nr. 1–19.
    Nr. 17 trägt zusätzlich `text`."""
    if nur_preise(df):
        return [rechnung_eintrag(df)] if (df.typ == "Position").any() else []
    pos = df[df.typ == "Position"]
    m = len(pos)
    ohne_kurz = ohne_lang = 0
    for r in pos.itertuples():
        if not normalisiere_leerzeichen(_txt(r.kurztext)):
            ohne_kurz += 1
        elif not normalisiere_leerzeichen(eigener_langtext(r.kurztext, r.langtext)):
            ohne_lang += 1
    mit_kurz = m - ohne_kurz
    nr12 = [(OHNE_KURZTEXT, ohne_kurz), (OHNE_LANGTEXT, ohne_lang)]
    return [
        _eintrag(1, mit_kurz - ohne_lang, m, nr12),
        _eintrag(2, mit_kurz - ohne_lang, m, nr12),
        _eintrag(3, mit_kurz, m, [(OHNE_KURZTEXT, ohne_kurz)]),
        _eintrag(4, m, m, []),
        _eintrag(5, mit_kurz, m, [(OHNE_KURZTEXT, ohne_kurz)]),
        _eintrag(6, mit_kurz, m, [(OHNE_KURZTEXT, ohne_kurz)]),
        # B2-Integration: Nr. 7–15, 18, 19 zitieren den Kurztext (R5); Nr. 16 vergleicht Kurz- und eigenen Langtext
        *[_eintrag(nr, mit_kurz, m, [(OHNE_KURZTEXT, ohne_kurz)]) for nr in (7, 8, 9, 10, 11, 12, 13, 14, 15)],
        _eintrag(16, mit_kurz - ohne_lang, m, nr12),
        rechnung_eintrag(df),
        *[_eintrag(nr, mit_kurz, m, [(OHNE_KURZTEXT, ohne_kurz)]) for nr in (18, 19)],
    ]


def text(e):
    """„prüfbar in 67 von 274 Positionen; übrige 207 ohne eigenen Langtext (…)“; Nr. 17: eigener Text."""
    if e.get("text"):
        return e["text"]
    t = f"prüfbar in {e['pruefbar']} von {e['gesamt']} Positionen"
    if e["gruende"]:
        t += "; übrige " + ", ".join(f"{n} {g}" for g, n in e["gruende"])
    return t


def eingeschraenkt(eintraege):
    """Einträge, bei denen nicht alle Positionen prüfbar sind (für den Hinweis im App-Kopf). Nr. 17 nicht: unbepreiste
    LVs sind der Normalfall; die Rechenprüfung steht immer eigens im Kopf (B1e)."""
    return [e for e in eintraege if e["pruefbar"] < e["gesamt"] and not e.get("text")]
