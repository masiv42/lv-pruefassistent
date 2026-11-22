"""
pruefung_struktur.py - Prüfungen Nr. 15 und 16 aus input/pruefkatalog.md (Block B1c, B1d; gebaut in Sitzung B2,
Team 21.11.2026, 18:50). Dateigetrennt; Einbindung in alle_pruefungen(), App und Export durch Sitzung B1.

  Nr. 15 Zulage ohne erkennbare Grundposition                                   Stufe 1, Rückfrage stellen
         Zulage = Kurztext beginnt mit „Zulage“, „Zul.“, „Zuschlag“ oder „Mehrpreis“ (wie das Merkmal „Zulage“ in
         lv_parser.art_from). Fund, wenn
         (a) die Zulage eine OZ nennt („zu Pos. 3.2.1“), die es im LV nicht gibt: nachweisbarer Fehler, oder
         (b) sie keine OZ nennt und in ihrem Abschnitt (OZ ohne letzte Stelle) vor ihr keine Position steht, die
             selbst keine Zulage ist: Unklarheit.
         Nennt die Zulage eine OZ, die es gibt, ist die Grundposition erkennbar: kein Fund. Ob die vorausgehende
         Position fachlich „passt“, prüft die Regel nicht.
  Nr. 16 Gleiche Leistung zweimal im selben Abschnitt                           Stufe 1, möglicher Widerspruch,
         Rückfrage stellen. Gleicher Kurztext, gleicher eigener Langtext (nicht leer, wie pruefabdeckung.py) und
         gleiche Einheit, verschiedene OZ, gleicher Abschnitt (OZ ohne letzte Stelle) und gleicher Titel.
         Ausgenommen: Bedarfs-, Wahl- und Alternativpositionen (Merkmal oder Fund Nr. 5) und Bezugstexte
         („wie vor“, „vorbeschrieben“, „jedoch“, „wie zuvor“, „wie Pos.“, „zuvor beschrieben“, „vorgenannt“,
         „oben beschrieben“), weil deren Inhalt erst mit der
         Vorposition feststeht (Fehlalarm-Falle: Angebot AN24-0305.pdf 3.1.20/3.1.60). Ein Fund je Gruppe mit allen
         Positionen; Belege = die gleichlautenden Texte (Kurztext, Anfang des Langtexts), am Original jeder
         Position geprüft.

Belege (R5): Kurztext als erster Beleg. Ausschnitte aus dem Langtext werden wie in pruefung_hinweise.py am
Original geprüft (PDF: PdfSeiten; GAEB 90: Gaeb90Bloecke). Rang in Stufe: RANG_VORSCHLAG, bestätigt (B2-F10).

Aufruf (aus der Projektwurzel, uv-Befehl siehe AGENTS.md):
  python src/pruefung_struktur.py <datei> [<datei> ...] [--out funde.json]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from lv_parser import parse
from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen, PdfSeiten, eigener_langtext, PRIORITAET_IN_STUFE
from pruefung_formal import nur_preise, sortiere, pruefe_formal
from pruefung_hinweise import Gaeb90Bloecke, ausschnitt, _txt, _seite, FELDWERT

FEHLER, WIDERSPRUCH, UNKLARHEIT = "nachweisbarer Fehler", "möglicher Widerspruch", "Unklarheit"
STUFE = 1
EMPFEHLUNG = "Rückfrage stellen"
# Rang in Stufe 1, endgültige Rangtabelle (Team 21.11.2026, 21:20; ersetzt F10): Nr. 17 → 1, Nr. 4 → 2, Nr. 3 → 3,
# Nr. 16 → 4, Nr. 2 → 5, Nr. 15 → 6, Nr. 1 → 7. Bei der Integration eine zentrale Tabelle (Sitzung B1).
RANG_VORSCHLAG = {16: 4, 15: 6}
TITEL = {15: "Zulage ohne erkennbare Grundposition", 16: "Gleiche Leistung zweimal im selben Abschnitt"}
KOSTENWIRKUNG = {
    15: "indirekt: Ohne erkennbare Grundposition ist unklar, auf welche Menge und Leistung der Zuschlag "
        "kalkuliert wird; Höhe nicht bezifferbar.",
    16: "direkt möglich: Ist dieselbe Leistung zweimal ausgeschrieben, wird sie zweimal angeboten; ist sie gewollt "
        "getrennt, fehlt im Text die Abgrenzung. Höhe = Positionspreis, nicht bezifferbar ohne Preise.",
}

ZULAGE_RE = re.compile(r"\s*(?:zulage|zul\.|zuschlag|mehrpreis)", re.I)
OZ_VERWEIS_RE = re.compile(r"\b(?:Pos\.?|Position|OZ|Ordnungszahl)\s*(?:Nr\.?\s*)?(\d+(?:\s*\.\s*\d+)+)\.?", re.I)
BEZUG_RE = re.compile(r"\bwie\s+vor|vorbeschrieben|\bjedoch\b|\bwie\s+zuvor\b|\bwie\s+Pos|\bzuvor\s+beschrieben"
                      r"|\bvorgenannt|\boben\s+beschrieben", re.I)
SONDER_RE = re.compile(r"alternativ|wahlposition|bedarfsposition|eventualposition", re.I)
LANG_WOERTER = 12          # Nr. 16: Anfang des gleichlautenden Langtexts als Beleg (höchstens so viele Wörter)


def ist_zulage(kurz):
    return bool(ZULAGE_RE.match(kurz or ""))


def abschnitt(oz):
    n = normalisiere_oz(oz)
    return n.rsplit(".", 1)[0] if "." in n else ""


def _position(r):
    return {"datei": r.datei, "oz": r.oz, "seite": _seite(r.seite)}


def _fund(nr, kategorie, zeilen, belege, feldbelege, begruendung):
    return {
        "id": f"{nr}|{zeilen[0].datei}|{normalisiere_oz(zeilen[0].oz)}",
        "pruefung": nr,
        "kategorie": kategorie,
        "titel": TITEL[nr],
        "positionen": [_position(r) for r in zeilen],
        "belege": belege,
        "feldbelege": feldbelege,
        "begruendung": f"{begruendung} Empfehlung laut Prüfkatalog: {EMPFEHLUNG}.",
        "stufe": STUFE,
        "stufe_begruendung": f"Stufe {STUFE} laut input/pruefkatalog.md, Nr. {nr}",
        "prioritaet_in_stufe": PRIORITAET_IN_STUFE[(nr, STUFE)],     # zentrale Rangtabelle (Team 21:20)
        "rueckfrage": None,
        "status": "offen",
    }


def _passt_fuer(r, seiten, bloecke):
    if seiten is not None and _seite(r.seite) is not None:
        return lambda a, s=_seite(r.seite): seiten.auf_einer_seite(a, s)
    if bloecke is not None:
        return lambda a, oz=r.oz: bloecke.im_block(a, oz)
    return lambda a: True


def _beleg_ausschnitt(text, m, passt):
    """Größter wörtlicher Ausschnitt um den Treffer, der am Original passt (wie pruefung_hinweise.treffer)."""
    for v, n in sorted(((v, n) for v in range(7) for n in range(5)), key=lambda vn: (-(vn[0] + vn[1]), -vn[0])):
        a = ausschnitt(text, m, v, n)
        if passt(a):
            return a
    return None


def _nr15(pos, seiten, bloecke):
    funde = []
    alle_oz = {normalisiere_oz(o) for o in pos.oz}
    zeilen = list(pos.itertuples())
    for i, r in enumerate(zeilen):
        kurz = normalisiere_leerzeichen(_txt(r.kurztext))
        if not kurz or not ist_zulage(kurz):
            continue
        lang = normalisiere_leerzeichen(eigener_langtext(_txt(r.kurztext), _txt(r.langtext)))
        verweise = []
        for quelle, text in (("kurz", kurz), ("lang", lang)):
            for m in OZ_VERWEIS_RE.finditer(text):
                verweise.append((quelle, text, m, re.sub(r"\s", "", m.group(1))))
        if verweise:
            fehlend = [v for v in verweise if normalisiere_oz(v[3]) not in alle_oz]
            if len(fehlend) < len(verweise) or not fehlend:
                continue                                  # mindestens eine genannte OZ gibt es: erkennbar
            passt = _passt_fuer(r, seiten, bloecke)
            belege = [kurz]
            for quelle, text, m, oz in fehlend:
                z = kurz if quelle == "kurz" else _beleg_ausschnitt(text, m, passt)
                if z and z not in belege:
                    belege.append(z)
            if len(belege) == 1 and not any(q == "kurz" for q, *_ in fehlend):
                continue                                  # Verweis nicht wörtlich belegbar (R5)
            genannt = ", ".join(sorted({v[3] for v in fehlend}))
            funde.append(_fund(15, FEHLER, [r], belege, [],
                               f"Die Zulage nennt die OZ {genannt}; diese OZ gibt es im LV nicht."))
            continue
        g = abschnitt(r.oz)
        vorher = [q for q in zeilen[:i] if abschnitt(q.oz) == g
                  and not ist_zulage(normalisiere_leerzeichen(_txt(q.kurztext)))]
        if vorher:
            continue
        funde.append(_fund(15, UNKLARHEIT, [r], [kurz], [],      # Fehlen = Begründung, kein Feldwert
                           f"Im Abschnitt {g or '(oberste Ebene)'} steht vor der Zulage keine Position, auf die "
                           f"sie sich beziehen kann, und sie nennt keine OZ. Worauf sich der Zuschlag bezieht, "
                           f"ist offen."))
    return funde


def _nr16(pos, bedarf, seiten, bloecke):
    gruppen = defaultdict(list)
    for r in pos.itertuples():
        kurz = normalisiere_leerzeichen(_txt(r.kurztext))
        lang = normalisiere_leerzeichen(eigener_langtext(_txt(r.kurztext), _txt(r.langtext)))
        if not kurz or not lang:
            continue                                      # nur Positionen mit eigenem Langtext
        if any(a in _txt(r.art) for a in ("Bedarf", "Wahl")) or normalisiere_oz(r.oz) in bedarf \
                or SONDER_RE.search(kurz + " " + lang + " " + _txt(r.art_roh)):
            continue
        if BEZUG_RE.search(kurz + " " + lang):
            continue
        gruppen[(abschnitt(r.oz), _txt(r.titel), kurz, lang, _txt(r.einheit))].append(r)
    funde = []
    for (g, _, kurz, lang, einheit), zeilen in gruppen.items():
        if len({normalisiere_oz(r.oz) for r in zeilen}) < 2:
            continue                                      # gleiche OZ ist Nr. 4, nicht Nr. 16
        woerter = list(re.finditer(r"\S+", lang))
        beleg_lang = None
        for n in range(min(LANG_WOERTER, len(woerter)), 0, -1):
            z = lang[:woerter[n - 1].end()]
            if all(_passt_fuer(r, seiten, bloecke)(z) for r in zeilen):
                beleg_lang = z
                break
        belege = [kurz] + ([beleg_lang] if beleg_lang and beleg_lang != kurz else [])
        feld = [{"art": FELDWERT, "text": f"OZ: {r.oz}"} for r in zeilen]
        feld.append({"art": FELDWERT, "text": f"Einheit: {_txt(zeilen[0].einheit_roh).strip() or einheit}"})
        ozs = ", ".join(r.oz for r in zeilen)
        funde.append(_fund(16, WIDERSPRUCH, zeilen, belege, feld,
                           f"Die Positionen {ozs} im Abschnitt {g} haben denselben Kurztext, denselben Langtext "
                           f"und dieselbe Einheit. Möglicherweise ist dieselbe Leistung zweimal ausgeschrieben; "
                           f"ist die Trennung gewollt, fehlt im Text die Abgrenzung."))
    return funde


def pruefe_struktur(df, quelle=None, weitere_funde=None):
    """Prüfungen Nr. 15 und 16 auf einer Tabelle aus parse(), sortiert wie alle_pruefungen().
    `quelle`: Pfad der Originaldatei; bei PDF und GAEB 90 Pflicht. `weitere_funde`: Funde Nr. 1–6 derselben Datei
    (für den Ausschluss von Bedarfspositionen, Nr. 5); fehlt die Liste, rechnet die Funktion pruefe_formal()."""
    if nur_preise(df):
        return []
    formate = set(df.format)
    if formate & {"PDF", "GAEB 90"} and quelle is None:
        raise ValueError("Für PDF und GAEB 90 den Pfad der Originaldatei angeben: pruefe_struktur(df, pfad)")
    if weitere_funde is None:
        weitere_funde = pruefe_formal(df)
    bedarf = {normalisiere_oz(p["oz"]) for f in weitere_funde if f["pruefung"] == 5 for p in f["positionen"]}
    pos = df[df.typ == "Position"]
    if "PDF" in formate:
        import pdfplumber
        with pdfplumber.open(str(quelle)) as pdf:
            seiten = PdfSeiten(pdf)
            return sortiere(_nr15(pos, seiten, None) + _nr16(pos, bedarf, seiten, None))
    bloecke = Gaeb90Bloecke(quelle) if "GAEB 90" in formate else None
    return sortiere(_nr15(pos, None, bloecke) + _nr16(pos, bedarf, None, bloecke))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Prüfungen Nr. 15 und 16")
    ap.add_argument("dateien", nargs="+")
    ap.add_argument("--out", help="Funde als JSON in diese Datei (nie in data/)")
    a = ap.parse_args()
    alle = []
    for d in a.dateien:
        df = parse(d)
        if nur_preise(df):
            print(f"{Path(d).name}: nur Preise, keine Prüfung", file=sys.stderr)
            continue
        f = pruefe_struktur(df, d)
        print(f"{Path(d).name}: {len(f)} Funde " + str(dict(sorted(Counter(x['pruefung'] for x in f).items()))),
              file=sys.stderr)
        alle += f
    text = json.dumps(alle, ensure_ascii=False, indent=2)
    if a.out:
        if Path(a.out).resolve().is_relative_to(Path("data").resolve()):
            sys.exit("--out nie in data/ (E12 (4))")
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
