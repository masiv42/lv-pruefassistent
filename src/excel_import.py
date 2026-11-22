"""
excel_import.py - Block B4: Excel-Import mit Spalten-Zuordnung (Sitzung B2, Team 21.11.2026, 18:50).

KENNZEICHNUNG: ohne Orga-Beispiel getestet. Es gibt im Datensatz keine Excel-LV (L14); getestet ist nur mit selbst
erzeugten Dateien (src/test_excel_import.py), darunter eine Rundreise parse() → Excel → lies_excel().

Ausgabe exakt wie parse() (src/lv_parser.py, docs/data-contracts.md): pandas DataFrame mit den Spalten COLUMNS,
eine Zeile je Titel oder Position, `format` = „Excel“ (neuer Wert, Vorschlag für den Datenvertrag), `seite` leer,
`einheit` normalisiert wie im Parser (norm_unit), `einheit_roh` wie in der Zelle, `art` wie im Parser (art_from),
`art_roh` leer, `titel` = Pfad der übergeordneten Titel („A > B“, je höchstens 80 Zeichen wie im Parser).

Spalten-Zuordnung:
  zuordnung = {"oz": "Pos.-Nr.", "kurztext": "Bezeichnung", ...}   ausdrücklich (hat Vorrang)
  spalten_vorschlag(kopf)                                          Vorschlag aus den Spaltenköpfen (fester Wortlaut,
                                                                   keine Ähnlichkeitssuche, damit gleich bleibt, E14)
  Pflicht: oz und kurztext. Optional: langtext, menge, einheit, ep, gp, typ.
Titel oder Position: mit Spalte `typ` („Titel“, „T“, „Bereich“, „Los“ → Titel, sonst Position); ohne Spalte ist eine
Zeile Titel, wenn sie weder Menge noch Einheit hat und ihre OZ Präfix einer anderen OZ ist (z. B. „1.1“ zu „1.1.10“;
auch Titel, die in einer Zusammenstellung am Ende wiederholt werden).
Zahlen: Zahlenzellen direkt; Text wie im Parser („3.200,000“ → 3200.0, de_number). OZ als Text lesen: Excel-Zahl 1.10
würde zu „1.1“ (Grenze, in der App als Hinweis zeigen).

Aufruf: python src/excel_import.py <datei.xlsx> [--blatt NAME] [--map oz=Pos. kurztext=Bezeichnung ...]
"""
import sys
from pathlib import Path

import pandas as pd

from lv_parser import COLUMNS, norm_unit, de_number, art_from, make_row, fingerprint

FORMAT = "Excel"
KENNZEICHNUNG = "Excel-Import: ohne Orga-Beispiel getestet"
FELDER = ("oz", "kurztext", "langtext", "menge", "einheit", "ep", "gp", "typ")
PFLICHT = ("oz", "kurztext")
# Spaltenköpfe je Feld (klein geschrieben, ohne Leerzeichen am Rand); erster Treffer in Reihenfolge der Tabelle zählt
KOEPFE = {
    "oz": ("oz", "ordnungszahl", "pos.", "pos", "pos.-nr.", "pos.nr.", "pos-nr", "position", "positionsnummer", "nr."),
    "kurztext": ("kurztext", "bezeichnung", "leistung", "leistungsbeschreibung (kurz)", "text", "kurzbeschreibung"),
    "langtext": ("langtext", "beschreibung", "leistungsbeschreibung", "langbeschreibung"),
    "menge": ("menge", "lv-menge", "anzahl"),
    "einheit": ("einheit", "me", "mengeneinheit", "eh"),
    "ep": ("ep", "einheitspreis", "ep (€)", "ep in eur", "e.p."),
    "gp": ("gp", "gesamtpreis", "gp (€)", "gp in eur", "g.p.", "gesamtbetrag"),
    "typ": ("typ", "art", "zeilenart", "satzart"),
}
TITEL_WERTE = {"titel", "t", "bereich", "los", "abschnitt", "gruppe"}


def spalten_vorschlag(kopf):
    """Feld -> Spaltenname für bekannte Spaltenköpfe. Jede Spalte höchstens einem Feld."""
    vorschlag, belegt = {}, set()
    norm = [(str(k), str(k).strip().lower()) for k in kopf]
    for feld in FELDER:
        for k, n in norm:
            if n in KOEPFE[feld] and k not in belegt:
                vorschlag[feld] = k
                belegt.add(k)
                break
    return vorschlag


def _text(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()


def _zahl(x):
    if x is None or (isinstance(x, float) and pd.isna(x)) or (isinstance(x, str) and not x.strip()):
        return None
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    return de_number(str(x).strip())


def _teile(oz):
    return [p for p in oz.strip(".").split(".") if p != ""]


def lies_excel(pfad, zuordnung=None, blatt=0, kopfzeile=0):
    """Excel-LV einlesen; Rückgabe wie parse(). `zuordnung`: Feld -> Spaltenname (sonst spalten_vorschlag)."""
    roh = pd.read_excel(pfad, sheet_name=blatt, header=kopfzeile, dtype=object, engine="openpyxl")
    roh.columns = [str(c) for c in roh.columns]
    zu = spalten_vorschlag(roh.columns)
    zu.update(zuordnung or {})
    unbekannt = sorted(f for f in zu if f not in FELDER)
    fehlt = [f for f in PFLICHT if f not in zu]
    falsch = sorted(s for s in zu.values() if s not in roh.columns)
    if unbekannt or fehlt or falsch:
        raise ValueError(f"Spalten-Zuordnung unvollständig: fehlt {fehlt}, unbekannte Felder {unbekannt}, "
                         f"Spalten nicht in der Tabelle {falsch}; vorhanden: {list(roh.columns)}")
    datei = Path(pfad).name
    zeilen = []
    for _, z in roh.iterrows():
        wert = lambda f: z[zu[f]] if f in zu else None
        oz, kurz = _text(wert("oz")), _text(wert("kurztext"))
        if not oz and not kurz:
            continue                                               # Leerzeile
        einheit_roh = _text(wert("einheit"))
        zeilen.append({"oz": oz, "kurz": kurz, "lang": _text(wert("langtext")), "menge": _zahl(wert("menge")),
                       "einheit_roh": einheit_roh, "ep": _zahl(wert("ep")), "gp": _zahl(wert("gp")),
                       "typ": _text(wert("typ")).lower() if "typ" in zu else None})
    for z in zeilen:
        if z["typ"] is not None:
            z["ist_titel"] = z["typ"] in TITEL_WERTE
        else:
            t = _teile(z["oz"])
            z["ist_titel"] = (z["menge"] is None and not z["einheit_roh"] and bool(t) and any(
                _teile(w["oz"])[:len(t)] == t and len(_teile(w["oz"])) > len(t) for w in zeilen))
    titel = {}                                                     # OZ-Teile (Tupel) -> Titeltext
    rows = []
    for z in zeilen:
        t = _teile(z["oz"])
        pfad_titel = [titel[tuple(t[:k])][:80] for k in range(1, len(t)) if tuple(t[:k]) in titel]
        if z["ist_titel"]:
            titel[tuple(t)] = z["kurz"]
            rows.append(make_row(datei=datei, format=FORMAT, typ="Titel", oz=z["oz"], titel=" > ".join(pfad_titel),
                                 kurztext=z["kurz"], langtext=z["lang"] or z["kurz"]))
            continue
        einheit = norm_unit(z["einheit_roh"])
        rows.append(make_row(datei=datei, format=FORMAT, typ="Position", oz=z["oz"], titel=" > ".join(pfad_titel),
                             kurztext=z["kurz"], langtext=z["lang"], menge=z["menge"], einheit=einheit,
                             einheit_roh=z["einheit_roh"], ep=z["ep"], gp=z["gp"],
                             art=art_from(z["kurz"], z["lang"], einheit), art_roh=""))
    return pd.DataFrame(rows, columns=COLUMNS)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=KENNZEICHNUNG)
    ap.add_argument("datei")
    ap.add_argument("--blatt", default=0)
    ap.add_argument("--map", nargs="*", default=[], help="feld=Spaltenname")
    a = ap.parse_args()
    zuordnung = dict(m.split("=", 1) for m in a.map)
    df = lies_excel(a.datei, zuordnung, a.blatt)
    pos = df[df.typ == "Position"]
    print(f"{a.datei}: {KENNZEICHNUNG} | {len(pos)} Positionen, {len(df) - len(pos)} Titel | Prüfsumme {fingerprint(df)}")
