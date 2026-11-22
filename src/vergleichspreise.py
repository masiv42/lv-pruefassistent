"""
vergleichspreise.py - Block B6b: Vergleichspreise nur aus bepreisten Dateien des Datensatzes, immer mit Quelle
(Datei, OZ, EP). Sitzung B2, Team 21.11.2026, 18:50; Scope D / T1 / E9.

Keine eigene Preisbildung: kein Mittelwert, kein Median, keine Spanne, keine Gewichtung, keine Empfehlung. Die
Funktion listet nur Positionen anderer Dateien mit ihrem Einheitspreis, so wie er in der Datei steht.

Quellen: Positionen mit Kurztext und EP > 0 aus den übergebenen Dateien (im Datensatz bepreist: Abgabe LV.pdf,
Angebot AN24-0305.pdf, StBALV23040.D86, [ORT_024] LV24069.D86; die Preisdateien StBALV23040.D84 und
Angebot AN24-0305.D84 haben keinen Kurztext und sind deshalb nicht suchbar).
Treffer (gleiche normalisierte Einheit ist immer Pflicht):
  „gleicher Kurztext“    Kurztext gleich (Groß-/Kleinschreibung und Leerraum egal)
  „alle Wörter enthalten“ jedes Wort des Suchtexts mit mindestens 3 Zeichen kommt im Kurztext der Quelle vor
Reihenfolge: Trefferart, Datei, OZ (fest, E14). Die Position selbst (gleiche Datei und OZ) ist ausgenommen.
Hinweis für die Anzeige: Preise ohne Datum, Region und Mengenbezug; mehrere Dateien können dasselbe Angebot in
verschiedenen Formaten sein (z. B. Abgabe LV.pdf und StBALV23040.D86).
"""
import re
import sys
from pathlib import Path

import pandas as pd

from lv_parser import parse, norm_unit
from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen
from pruefung_formal import oz_sortkey

GLEICH, WOERTER = "gleicher Kurztext", "alle Wörter enthalten"
HINWEIS = ("Vergleichspreise aus bepreisten Dateien des Datensatzes, unverändert mit Quelle (Datei, OZ, EP). "
           "Ohne Datum, Region und Mengenbezug; keine Preisbildung durch das Tool.")
SPALTEN = ["datei", "oz", "kurztext", "einheit", "menge", "ep", "gp"]


def _norm(t):
    return normalisiere_leerzeichen(t if isinstance(t, str) else "").lower()


def _woerter(t):
    return set(re.findall(r"[0-9a-zäöüß]{3,}", _norm(t)))


def preisquellen(dateien):
    """Tabelle der bepreisten Positionen (Kurztext und EP > 0) aus den Dateien, Spalten SPALTEN."""
    teile = []
    for d in sorted(dateien, key=lambda p: Path(p).name):
        df = parse(str(d))
        pos = df[(df.typ == "Position") & (df.ep.fillna(0) > 0)
                 & df.kurztext.fillna("").map(lambda k: bool(normalisiere_leerzeichen(k)))]
        teile.append(pos[SPALTEN])
    return pd.concat(teile, ignore_index=True) if teile else pd.DataFrame(columns=SPALTEN)


def vergleichspreise(kurztext, einheit, quellen, ohne=None, max_treffer=20):
    """Liste von {datei, oz, kurztext, einheit, menge, ep, gp, trefferart, quelle}. `ohne` = (datei, oz) der
    gesuchten Position, die nicht als eigener Vergleich erscheinen soll."""
    such, e = _norm(kurztext), norm_unit(einheit or "")
    sw = _woerter(kurztext)
    if not such:
        return []
    treffer = []
    for r in quellen.itertuples():
        if norm_unit(r.einheit or "") != e:
            continue
        if ohne and r.datei == ohne[0] and normalisiere_oz(r.oz) == normalisiere_oz(ohne[1]):
            continue
        k = _norm(r.kurztext)
        art = GLEICH if k == such else (WOERTER if sw and sw <= _woerter(r.kurztext) else None)
        if art is None:
            continue
        treffer.append({"datei": r.datei, "oz": r.oz, "kurztext": normalisiere_leerzeichen(r.kurztext),
                        "einheit": r.einheit, "menge": None if pd.isna(r.menge) else float(r.menge),
                        "ep": float(r.ep), "gp": None if pd.isna(r.gp) else float(r.gp), "trefferart": art,
                        "quelle": f"{r.datei}, OZ {r.oz}, EP {_eur(r.ep)}"})
    treffer.sort(key=lambda t: (t["trefferart"] != GLEICH, t["datei"], oz_sortkey(t["oz"])))
    return treffer[:max_treffer]


def _eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Vergleichspreise aus bepreisten Dateien (mit Quelle)")
    ap.add_argument("kurztext")
    ap.add_argument("einheit")
    ap.add_argument("dateien", nargs="+")
    a = ap.parse_args()
    print(HINWEIS)
    for t in vergleichspreise(a.kurztext, a.einheit, preisquellen(a.dateien)):
        print(f"{t['trefferart']:<22} {t['quelle']}  „{t['kurztext'][:60]}“")
