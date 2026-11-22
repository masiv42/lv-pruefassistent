"""
test_vergleichspreise.py - Tests für src/vergleichspreise.py (Block B6b, Sitzung B2).

  1. kleine Tabellen: Trefferarten, Einheit Pflicht, eigene Position ausgenommen, Reihenfolge, keine Preisbildung
  2. echte Dateien: Quellen nur aus bepreisten Dateien; Beispiele aus unbepreisten LVs (Leistungsverzeichnis.pdf,
     Leistungsverzeichnis_leer.pdf, [NUMMER_001]_leer.X83) finden Preise mit Quelle
  3. Skeptiker am Original: jeder gezeigte EP von 5+ Treffern steht in der Rohdatei an dieser OZ (PDF: Seitentext
     im Block von der OZ-Zeile bis zur nächsten OZ-Zeile, z. B. Mengenzeile „1,000 St 26.000,000 26.000,00“; GAEB 90: Satz 23 der OZ, EP-Feld), ohne parse()
  4. Doppellauf gleich (E14)
Aufruf aus src/:  python test_vergleichspreise.py <data/raw>
"""
import ast
import re
from itertools import takewhile
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

from lv_parser import parse
from vergleichspreise import vergleichspreise, preisquellen, GLEICH, WOERTER, SPALTEN, HINWEIS

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
BEPREIST = ["Abgabe LV.pdf", "Angebot AN24-0305.pdf", "StBALV23040.D86", "[ORT_024] LV24069.D86",
            "StBALV23040.D84", "Angebot AN24-0305.D84"]
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def test_klein():
    q = pd.DataFrame([
        {"datei": "B.pdf", "oz": "2.1", "kurztext": "Boden lösen", "einheit": "m³", "menge": 10.0, "ep": 12.5, "gp": 125.0},
        {"datei": "A.pdf", "oz": "1.10", "kurztext": "Boden lösen und laden", "einheit": "m³", "menge": 5.0, "ep": 15.0, "gp": 75.0},
        {"datei": "A.pdf", "oz": "1.2", "kurztext": "BODEN  lösen", "einheit": "m3", "menge": 1.0, "ep": 11.0, "gp": 11.0},
        {"datei": "A.pdf", "oz": "1.3", "kurztext": "Boden lösen", "einheit": "t", "menge": 1.0, "ep": 9.0, "gp": 9.0},
        {"datei": "C.pdf", "oz": "7.7", "kurztext": "Boden lösen", "einheit": "m³", "menge": 1.0, "ep": 99.0, "gp": 99.0},
    ], columns=SPALTEN)
    t = vergleichspreise("Boden lösen", "m3", q, ohne=("C.pdf", "07.7"))
    check("Trefferarten und Reihenfolge (gleicher Kurztext vor Wörtern, dann Datei, OZ)",
          [(x["datei"], x["oz"], x["trefferart"]) for x in t] ==
          [("A.pdf", "1.2", GLEICH), ("B.pdf", "2.1", GLEICH), ("A.pdf", "1.10", WOERTER)], str(t))
    check("andere Einheit kein Treffer, eigene Position (OZ normalisiert) ausgenommen",
          not any(x["oz"] in ("1.3", "7.7") for x in t))
    check("Quelle mit Datei, OZ, EP", t[0]["quelle"] == "A.pdf, OZ 1.2, EP 11,00 €", t[0]["quelle"])
    check("EP unverändert aus der Quelle", [x["ep"] for x in t] == [11.0, 12.5, 15.0])
    check("leerer Suchtext: keine Treffer", vergleichspreise("", "m³", q) == [])
    check("max_treffer", len(vergleichspreise("Boden lösen", "m³", q, max_treffer=1)) == 1)
    quelle = Path(__file__).with_name("vergleichspreise.py").read_text(encoding="utf-8")
    code = ast.parse(quelle)
    namen = {n.id for n in ast.walk(code) if isinstance(n, ast.Name)} | \
            {n.attr for n in ast.walk(code) if isinstance(n, ast.Attribute)}
    check("keine eigene Preisbildung (kein mean/median/sum/min/max/statistics im Code)",
          not ({"mean", "median", "statistics", "quantile", "min", "max", "sum"} & namen), str(namen & {"mean", "median", "min", "max", "sum"}))
    check("Hinweis „keine Preisbildung durch das Tool“", "keine Preisbildung durch das Tool" in HINWEIS)


def ep_im_original(datei, oz, ep):
    """True, wenn der EP an dieser OZ in der Rohdatei steht (ohne parse())."""
    pfad = D / datei
    if pfad.suffix.lower() == ".pdf":
        text = re.sub(r"\s", "", f"{ep:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with pdfplumber.open(str(pfad)) as pdf:
            zeilen = [re.sub(r"\s", "", z) for p in pdf.pages for z in (p.extract_text() or "").split("\n")]
        oz_re = re.compile(r"^\.?\d+(?:\.\d+)+\.?\D")
        for i, z in enumerate(zeilen):
            if z.startswith(oz) and oz_re.match(z):
                block = [z] + list(takewhile(lambda y: not oz_re.match(y), zeilen[i + 1:i + 60]))
                if any(text in y for y in block):        # Block der Position bis zur nächsten OZ-Zeile
                    return True
        return False
    zeilen = pfad.read_bytes().decode("cp850").split("\n")
    roh = f"{round(ep * 100):010d}"
    return any(l[:2] == "23" and re.sub(r"\s", "", l[2:11]) == oz.replace(".", "") and roh in l[11:30] for l in zeilen)


if __name__ == "__main__":
    test_klein()
    q = preisquellen([D / n for n in BEPREIST])
    check("Quellen nur aus bepreisten Dateien mit Kurztext", set(q.datei) == {"Abgabe LV.pdf", "Angebot AN24-0305.pdf",
                                                                             "StBALV23040.D86", "[ORT_024] LV24069.D86"},
          str(sorted(set(q.datei))))
    print(f"       Preisquellen: {len(q)} Positionen " + str(q.datei.value_counts().to_dict()))
    beispiele = [("Leistungsverzeichnis.pdf", "1.1.150"), ("Leistungsverzeichnis.pdf", "3.1.20"),
                 ("Leistungsverzeichnis_leer.pdf", "1.1.1"), ("[NUMMER_001]_leer.X83", "1.1.1"),
                 ("[NUMMER_001]_leer.X83", "5.1.1")]
    gezeigt = []
    for datei, oz in beispiele:
        df = parse(str(D / datei))
        r = df[(df.typ == "Position") & (df.oz.map(lambda o: o.strip(".")) == oz)].iloc[0]
        t = vergleichspreise(r.kurztext, r.einheit, q, ohne=(datei, oz))
        print(f"       {datei} {oz} „{r.kurztext[:40]}“ {r.einheit}: {len(t)} Treffer " +
              "; ".join(f"{x['trefferart']}: {x['quelle']}" for x in t[:3]))
        check(f"Vergleichspreis gefunden für {datei} {oz}", bool(t))
        gezeigt += t[:2]
    zweit = vergleichspreise(r.kurztext, r.einheit, quellen=preisquellen([D / n for n in reversed(BEPREIST)]),
                             ohne=(datei, oz))
    check("Doppellauf mit umgekehrter Dateireihenfolge gleich (E14)",
          zweit == vergleichspreise(r.kurztext, r.einheit, q, ohne=(datei, oz)))
    for x in gezeigt:
        check(f"Skeptiker: EP {x['quelle']} im Original", ep_im_original(x["datei"], x["oz"], x["ep"]))
    check("Skeptiker: mindestens 5 Treffer geprüft", len(gezeigt) >= 5)
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
