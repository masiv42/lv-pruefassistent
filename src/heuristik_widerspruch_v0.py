"""
heuristik_widerspruch_v0.py - REFERENZ, nicht Endstand.

Diese Heuristik hat das Blatt "Widerspruch-Kandidaten" in
data/parsed/alle_LVs_geparst.xlsx erzeugt (19 Kandidaten: 15 DN, 4 Betonklasse).
Sie ist der Ausgangspunkt für die Prüfungen Nr. 1 und 2 aus input/pruefkatalog.md.

Logik je Position:
1. Werte im Kurztext suchen: Nennweiten (DN 100) und Betonklassen (C25/30).
2. Dieselben Werte im Langtext suchen. Beginnt der Langtext mit dem Kurztext
   (bei PDF immer der Fall, weil der Parser die erste Zeile als Kurztext nimmt),
   wird dieser Anfang vorher abgeschnitten. Sonst fände man den Kurztext-Wert
   im Langtext wieder und würde nie einen Widerspruch sehen.
3. Kandidat, wenn beide Seiten Werte haben und KEIN Wert gemeinsam ist.

Bekannte Grenzen:
- Fehlalarm, wenn der Langtext DN-Werte von Anbauteilen nennt
  (Beispiel: 501-24-01_GAEB-XML_sas.x83, 02.05.0007, Schacht DN 2500).
- Übersieht Fälle, in denen der Langtext den Kurztext-Wert UND einen anderen nennt.
- Normalisiert nur Leerzeichen ("DN 100" = "DN100"), keine Schreibvarianten wie "NW 100".

Aufruf: python heuristik_widerspruch_v0.py data/raw
"""
import re
import sys
from pathlib import Path

import pandas as pd

from lv_parser import parse

PATTERNS = {
    "DN": r"\bDN\s?\d{2,4}\b",
    "Beton": r"\bC\s?\d{2}/\d{2}\b",
}

# Auswahl wie in alle_LVs_geparst.xlsx: je LV genau eine Quelle
DATEIEN = [
    "8209.003_Leistungsverzeichnis_leer.X83",
    "[NUMMER_001]_leer.X83",
    "Leistungsverzeichnis.pdf",
    "GAEB-[PROJEKT_004].X83",
    "501-24-01_GAEB-XML_sas.x83",
]


def werte(pattern, text):
    return {re.sub(r"\s", "", x).upper() for x in re.findall(pattern, text or "", re.I)}


def kandidaten(df):
    """Gibt je Position die Kandidaten zurück (Spalte widerspruch_kandidat, leer = keiner)."""
    out = []
    for r in df.itertuples():
        kurz = r.kurztext or ""
        lang = r.langtext or ""
        if lang.startswith(kurz):
            lang = lang[len(kurz):]
        teile = []
        for name, pat in PATTERNS.items():
            k, l = werte(pat, kurz), werte(pat, lang)
            if k and l and not (k & l):
                teile.append(f"{name}: Kurztext {', '.join(sorted(k))} / Langtext {', '.join(sorted(l))}")
        out.append("; ".join(teile))
    return out


if __name__ == "__main__":
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
    files = DATEIEN + sorted(f.name for f in d.iterdir() if f.name.startswith("LV_"))
    frames = []
    for f in files:
        df = parse(d / f)
        df = df[df.typ == "Position"].copy()
        df["widerspruch_kandidat"] = kandidaten(df)
        frames.append(df[df.widerspruch_kandidat != ""])
    res = pd.concat(frames, ignore_index=True)
    print(f"{len(res)} Kandidaten")
    print(res[["datei", "oz", "widerspruch_kandidat"]].to_string(index=False))
