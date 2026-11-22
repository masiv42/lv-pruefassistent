"""
test_pruefung_vollstaendigkeit.py - Tests für src/pruefung_vollstaendigkeit.py (Block B3, Sitzung B2).

  1. kleine Tabellen: je Paarregel positiv (Auslöser ohne Gegenstück) und negativ (Gegenstück vorhanden,
     Gegenstück nur im Langtext des Auslösers, Fehlalarm-Fallen aus der Datenauswertung)
  2. echte Dateien: Fund LV_00 2.1.30 (R5), Fallen ohne Fund, Datenvertrag, R5, R7, höchstens 5 Regeln
  3. Doppellauf byte-gleich (E14)
  4. Skeptiker am Original: Beleg im Original (ohne parse()) und das Fehlen des Gegenstücks über alle Seiten bzw.
     den ganzen Text der Rohdatei (Kurztext-Zeilen)

Aufruf aus src/:  python test_pruefung_vollstaendigkeit.py <data/raw>
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import pdfplumber

from lv_parser import parse, COLUMNS
from pruefung_widerspruch import normalisiere_oz, beleg_im_text
from pruefung_vollstaendigkeit import pruefe_vollstaendigkeit, REGELN, NR, KOSTENWIRKUNG, HINWEIS, RANG_VORSCHLAG
from test_pruefung_hinweise import PdfOriginal

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
FELDER = ["id", "pruefung", "kategorie", "titel", "positionen", "belege", "feldbelege",
          "begruendung", "stufe", "stufe_begruendung", "prioritaet_in_stufe", "rueckfrage", "status"]
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, kurz, lang=""):
    z = {c: None for c in COLUMNS}
    z.update(datei="test.X83", format="GAEB XML", typ="Position", oz=oz, kurztext=kurz,
             langtext=(kurz + " " + lang).strip(), menge=1.0, einheit="St", einheit_roh="St", art="Normal")
    return z


def lauf(*z):
    return pruefe_vollstaendigkeit(pd.DataFrame(list(z), columns=COLUMNS))


def regeln(funde):
    return sorted({m for f in funde for m in re.findall(r"\bR[1-5]\b", f["begruendung"])})


def test_klein():
    check("höchstens 5 Paarregeln (Scope D)", len(REGELN) <= 5)
    check("Rangtabelle (Team 21:20): Nr. 19 → 5 in Stufe 3", RANG_VORSCHLAG == {(19, 3): 5})
    wand = zeile("1.1", "Stahlbetonwand C25/30, d=24cm", "Ortbeton, Schalung und Bewehrung in gesonderter Position")
    f = lauf(wand)
    check("R1+R2: Stahlbetonwand ohne Schalungs-/Bewehrungsposition → ein Fund mit beiden Regeln",
          len(f) == 1 and regeln(f) == ["R1", "R2"] and f[0]["belege"][0] == "Stahlbetonwand C25/30, d=24cm")
    check("Hinweistext und Kategorie", f and HINWEIS in f[0]["begruendung"] and f[0]["kategorie"] == "Risikohinweis")
    check("R1/R2 negativ: Schalung und Betonstahl als eigene Positionen",
          lauf(wand, zeile("1.2", "Schalung Wand"), zeile("1.3", "Betonstahl B500 liefern")) == [])
    check("R1/R2 negativ: Gegenstück nur im Langtext des Auslösers zählt nicht", bool(lauf(wand)))
    check("R1 negativ: „Beton … o.Schalung“ ist kein Gegenstück",
          regeln(lauf(wand, zeile("1.2", "Beton Köcher C30/37, o.Schalung"), zeile("1.3", "Betonstahl"))) == ["R1"])
    for neg in ("Voranstrich auf Ortbeton, Dampfsperre", "UHPC-Stahlbetonrohre DN 800 C80/95 verlegen",
                "Stahlbeton abbrechen C20/25", "Regiearbeiten Stahlbeton C25/30"):
        check(f"R1/R2 Falle ohne Fund: „{neg}“", lauf(zeile("1.1", neg)) == [] or "R1" not in regeln(lauf(zeile("1.1", neg))))
    rohr = zeile("2.1", "Druckrohr PE-HD DN 150 verlegen")
    check("R3: Druckrohr verlegen ohne Graben", regeln(lauf(rohr)) == ["R3"])
    check("R3 negativ: Rohrgraben vorhanden", lauf(rohr, zeile("2.2", "Rohrgraben ausheben, seitlich lagern")) == [])
    check("R3 negativ: Rohrleitungen im Estrich (kein Tiefbaurohr)",
          lauf(zeile("2.1", "Ausgleichsschicht EPS", "über Rohrleitungen verlegen")) == [])
    aus = zeile("3.1", "Baugrube ausheben")
    check("R4: Aushub ohne Abfuhr/Verfüllen", regeln(lauf(aus)) == ["R4"])
    check("R4 negativ: Abfuhr im eigenen Text", lauf(zeile("3.1", "Baugrube ausheben", "Boden laden, abfahren")) == [])
    check("R4 negativ: Zulage zu Aushub ist kein Auslöser", lauf(zeile("3.1", "Zulage Aushub Fels")) == [])
    asp = zeile("4.1", "Fräsen Asphalt, bituminös")
    check("R5: Asphalt fräsen ohne Wiederherstellung", regeln(lauf(asp)) == ["R5"])
    check("R5 negativ: Asphalttragschicht herstellen", lauf(asp, zeile("4.2", "Asphalttragschicht 0/32 einbauen")) == [])
    check("R5: „Teilentsorgung PAK-haltige Asphaltdecke“ ist kein Gegenstück",
          regeln(lauf(asp, zeile("4.2", "Teilentsorgung PAK-haltige Asphaltdecke"))) == ["R5"])
    f = lauf(zeile("5.1", "Position"), asp, zeile("5.2", "Asphalt aufbrechen"))
    check("ein Fund je Regel und LV, an der ersten Auslöser-Position",
          len(f) == 1 and f[0]["positionen"][0]["oz"] == "4.1" and "2 Auslöser-Positionen" in f[0]["begruendung"]
          and f[0]["feldbelege"] == [])
    check("ohne Kurztext kein Fund", lauf(zeile("1.1", "", "Fräsen Asphalt")) == [])


def original_kurztext_zeilen(pfad):
    """Alle Textzeilen der Rohdatei (PDF: Seitentext; GAEB: Text ohne Tags bzw. Satz 25), ohne parse()."""
    e = pfad.suffix.lower()
    if e == ".pdf":
        with pdfplumber.open(str(pfad)) as pdf:
            return [l for p in pdf.pages for l in (p.extract_text() or "").split("\n")]
    roh = pfad.read_bytes()
    if e.startswith(".x"):
        return re.sub(r"<[^>]+>", "\n", roh.decode("utf-8", "replace")).split("\n")
    return [l[2:72] for l in roh.decode("cp850").split("\n") if l[:2] == "25"]


if __name__ == "__main__":
    test_klein()
    cache = {p.name: parse(str(p)) for p in sorted(D.iterdir())
             if not p.name.startswith(".") and p.suffix.lower() != ".docx"}
    alle = [f for n in sorted(cache) for f in pruefe_vollstaendigkeit(cache[n], D / n)]
    print(f"       {len(alle)} Funde: " + "; ".join(f"{f['positionen'][0]['datei']} {f['positionen'][0]['oz']} "
                                                  f"{regeln([f])}" for f in alle))
    check("Fund LV_00 2.1.30 (R5 Asphalt fräsen, kein Asphalt herstellen)",
          [(f["positionen"][0]["datei"], f["positionen"][0]["oz"], regeln([f])) for f in alle]
          == [("LV_00_Roh_und_Erdauarbeiten.pdf", "2.1.30", ["R5"])])
    check("Datenvertrag", all(list(f) == FELDER and f["pruefung"] == NR and f["status"] == "offen" for f in alle))
    check("Kostenwirkung beschrieben", bool(KOSTENWIRKUNG))
    texte = {(n, normalisiere_oz(r.oz)): (r.kurztext or "", r.langtext or "")
             for n, df in cache.items() for r in df[df.typ == "Position"].itertuples()}
    check("R5 gegen parse()", all(beleg_im_text(b, *texte[(f["positionen"][0]["datei"],
                                                            normalisiere_oz(f["positionen"][0]["oz"]))])
                                  for f in alle for b in f["belege"]))
    check("R7", not [f for f in alle if VERBOTEN.search(f["titel"] + f["begruendung"])])
    zweit = {n: pruefe_vollstaendigkeit(cache[n], D / n) for n in reversed(sorted(cache))}
    check("Doppellauf byte-gleich (E14)", json.dumps(alle, ensure_ascii=False) ==
          json.dumps([f for n in sorted(cache) for f in zweit[n]], ensure_ascii=False))
    # Skeptiker
    for f in alle:
        p = f["positionen"][0]
        pdf = PdfOriginal(D / p["datei"]) if p["datei"].lower().endswith(".pdf") else None
        if pdf:
            check(f"Skeptiker: Belege {f['id']} im Original (S. {[pdf.finde(b, p['seite']) for b in f['belege']]})",
                  all(pdf.finde(b, p["seite"]) for b in f["belege"]))
        zeilen = original_kurztext_zeilen(D / p["datei"])
        for r in [r for r in REGELN if r["id"] in regeln([f])]:
            if r["gegen_im"] == "kurz":
                gegen = [l for l in zeilen if r["gegen"].search(l)
                         and not (r.get("gegen_ohne") and r["gegen_ohne"].search(l))]
                kompakt = [l for l in zeilen if r["gegen"].search(re.sub(r"(?<=\w) (?=\w)", "", l))
                           and not (r.get("gegen_ohne") and r["gegen_ohne"].search(l))]
                check(f"Skeptiker: im Original keine Zeile mit Gegenstück {r['id']} ({p['datei']})",
                      not gegen and not kompakt, str((gegen + kompakt)[:3]))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
