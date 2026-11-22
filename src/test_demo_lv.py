"""
test_demo_lv.py - Tests für src/demo_lv.py (Block B7, Sitzung B2). Demo-Datei nur im Temp-Ordner (E12 (4)).

  1. je Prüfung Nr. 1–19 ein Fund an der eingebauten OZ (Nr. 1–6: alle_pruefungen aus B1; Nr. 7–14, 18:
     pruefe_hinweise; Nr. 15/16: pruefe_struktur; Nr. 19: pruefe_vollstaendigkeit; Nr. 17: noch kein Modul (B1e) –
     geprüft wird, dass parse() Menge × EP ≠ GP liefert)
  2. Vorlage unverändert: Prüfsumme der Vorlage wie in data/qa/raw_pruefsummen.txt (E11); alle Zeilen der Vorlage
     stehen unverändert in parse() der Demo-Datei
  3. byte-gleich bei zweitem Erzeugen (E14); Ziel in data/raw wird abgelehnt
  4. Skeptiker: jeder Beleg der Demo-Funde steht wörtlich in der Demo-Datei (lxml, ohne parse())
Aufruf aus src/:  python test_demo_lv.py <data/raw>
"""
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from lv_parser import parse
from pruefung_widerspruch import normalisiere_oz
from pruefung_formal import alle_pruefungen
from pruefung_hinweise import pruefe_hinweise
from pruefung_struktur import pruefe_struktur
from pruefung_vollstaendigkeit import pruefe_vollstaendigkeit
from demo_lv import erzeuge, FAELLE, VORLAGE, ZIEL
from test_pruefung_hinweise import original_xml

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


if __name__ == "__main__":
    summen = (D.parent / "qa" / "raw_pruefsummen.txt").read_text(encoding="utf-8")
    soll = next(l.split()[0] for l in summen.splitlines() if l.rstrip().endswith(VORLAGE))
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pfad = erzeuge(D, tmp / "demo")
        check("Vorlage unverändert (E11, Prüfsumme wie raw_pruefsummen.txt)",
              hashlib.sha256((D / VORLAGE).read_bytes()).hexdigest() == soll)
        info = json.loads((tmp / "demo" / "demo_faelle.json").read_text(encoding="utf-8"))
        check("demo_faelle.json nennt Vorlage, Prüfsumme und Fälle", info["vorlage_sha256"] == soll
              and info["datei"] == ZIEL and len(info["faelle"]) == 19)
        zweit = erzeuge(D, tmp / "demo2")
        check("byte-gleich bei zweitem Erzeugen (E14)", pfad.read_bytes() == zweit.read_bytes())
        try:
            erzeuge(D, D / "x")
            check("Ziel in data/raw abgelehnt", False)
        except ValueError:
            check("Ziel in data/raw abgelehnt", True)
        df = parse(str(pfad))
        orig = parse(str(D / VORLAGE))
        alt = df[~df.oz.str.match(r"^(98|99)(\.|$)")].drop(columns="datei").reset_index(drop=True)
        leer = lambda t: t.astype(object).where(t.notna(), None)      # NaN und None = leer (ep/gp-Spalten)
        check("alle Zeilen der Vorlage unverändert in der Demo-Datei", leer(alt).equals(leer(orig.drop(columns="datei"))))
        f16 = alle_pruefungen(df, pfad)
        funde = f16 + pruefe_hinweise(df, pfad, f16) + pruefe_struktur(df, pfad, f16) + pruefe_vollstaendigkeit(df, pfad)
        orte = defaultdict(set)
        for f in funde:
            for p in f["positionen"]:
                orte[f["pruefung"]].add(normalisiere_oz(p["oz"]))
        for nr in sorted(FAELLE):
            if nr == 17:
                r = df[(df.typ == "Position") & (df.oz == FAELLE[17])].iloc[0]
                check(f"Nr. 17 Fall {FAELLE[17]}: Menge × EP ≠ GP in parse() ({r.menge} × {r.ep} ≠ {r.gp})",
                      r.menge * r.ep != r.gp and (r.menge, r.ep, r.gp) == (10.0, 5.0, 60.0))
                continue
            check(f"Nr. {nr}: Fund an {FAELLE[nr]}", normalisiere_oz(FAELLE[nr]) in orte[nr],
                  f"Funde Nr. {nr} an {sorted(orte[nr])[:6]}")
        neu = [f for f in funde if any(p["oz"].startswith(("98.", "99.")) for p in f["positionen"])]
        o = original_xml(pfad)                    # je OZ ein Item; doppelte OZ (Fall Nr. 4) über alle Items der OZ
        from lxml import etree
        items = defaultdict(str)
        for it in etree.parse(str(pfad)).getroot().iter("{*}Item"):
            ctgy = it.getparent().getparent().getparent()
            items[normalisiere_oz(ctgy.get("RNoPart") + "." + it.get("RNoPart"))] += " " + " ".join(
                " ".join(it.find("{*}Description").itertext()).split())
        fehlt = [(f["id"], b) for f in neu for p in f["positionen"] for b in f["belege"]
                 if b not in o[normalisiere_oz(p["oz"])][1] and b not in items[normalisiere_oz(p["oz"])]]
        check(f"Skeptiker: alle Belege der {len(neu)} Demo-Funde wörtlich in der Demo-Datei", not fehlt, str(fehlt[:3]))
        print("       Demo-Funde je Prüfung: " + str({nr: sorted(o_ for o_ in orte[nr] if o_.startswith(("98", "99")))
                                                      for nr in sorted(orte)}))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
