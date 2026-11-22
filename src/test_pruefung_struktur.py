"""
test_pruefung_struktur.py - Tests für src/pruefung_struktur.py (Nr. 15 und 16, Block B1c/B1d, Sitzung B2).

  1. kleine Tabellen: Positiv- und Negativfälle (Fehlalarm-Fallen aus den Vorgaben des Teams, 21.11.2026, 18:50)
  2. echte Dateien: Vorgaben (3 Zulagen ohne Grundposition, Kandidat LV_00 3.2.100/3.2.195, Fallen
     Angebot AN24-0305.pdf 3.1.20/3.1.60 und 501-24-01…x83 02.03.0005/0007), Datenvertrag, R5, R7, Sortierung
  3. Doppellauf (E14), byte-gleich, zweiter Lauf in umgekehrter Dateireihenfolge
  4. Skeptiker am Original für jeden Beleg jeder Position jedes Funds (ohne parse(); Leser aus
     test_pruefung_hinweise.py: GAEB XML per lxml, GAEB 90 zeilenweise, PDF-Seitentext ohne Leerzeichen)

Aufruf aus src/ (uv-Befehl siehe AGENTS.md):  python test_pruefung_struktur.py <data/raw> [--bericht ziel.json]
Exit-Code 0 = alle Tests bestanden. Schreibt nichts in data/ (E12 (4)).
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from lv_parser import parse, COLUMNS
from pruefung_widerspruch import normalisiere_oz, normalisiere_leerzeichen, beleg_im_text
from pruefung_formal import nur_preise, sortiere
from pruefung_struktur import (pruefe_struktur, ist_zulage, RANG_VORSCHLAG, KOSTENWIRKUNG, FEHLER, WIDERSPRUCH,
                               UNKLARHEIT)
from test_pruefung_hinweise import original_xml, original_gaeb90, PdfOriginal

D = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("data/raw")
BERICHT = sys.argv[sys.argv.index("--bericht") + 1] if "--bericht" in sys.argv else None
FELDER = ["id", "pruefung", "kategorie", "titel", "positionen", "belege", "feldbelege",
          "begruendung", "stufe", "stufe_begruendung", "prioritaet_in_stufe", "rueckfrage", "status"]
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, kurz="Position", lang="", einheit="St", art="Normal", titel="T", art_roh="", menge=1.0):
    z = {c: None for c in COLUMNS}
    z.update(datei="test.X83", format="GAEB XML", typ="Position", oz=oz, kurztext=kurz,
             langtext=(kurz + " " + lang).strip() if lang else kurz, menge=menge, einheit=einheit,
             einheit_roh=einheit, art=art, art_roh=art_roh, titel=titel)
    return z


def tab(*z):
    return pd.DataFrame(list(z), columns=COLUMNS)


def nrn(funde, nr):
    return [f for f in funde if f["pruefung"] == nr]


# --------------------------------------------------------------------------- 1. kleine Tabellen

def test_klein():
    check("Rang in Stufe 1 laut Rangtabelle (Team 21:20): Nr. 16 → 4, Nr. 15 → 6", RANG_VORSCHLAG == {16: 4, 15: 6})
    check("Zulage erkannt: Zulage, Zul., Zuschlag, Mehrpreis",
          all(ist_zulage(k) for k in ("Zulage Entsorgung", "Zul.Deckenschalung,SB2", "Zuschlag Nachtarbeit",
                                      "Mehrpreis Oberfläche")) and not ist_zulage("Beton, Zulage für Sichtbeton"))
    f = pruefe_struktur(tab(zeile("1.1.1", "Zulage Entsorgung"), zeile("1.1.2", "Boden lösen")))
    check("Nr. 15: Zulage als erste Position im Abschnitt, Kategorie Unklarheit, Beleg Kurztext",
          len(nrn(f, 15)) == 1 and nrn(f, 15)[0]["kategorie"] == UNKLARHEIT
          and nrn(f, 15)[0]["belege"] == ["Zulage Entsorgung"]
          and nrn(f, 15)[0]["feldbelege"] == [] and "keine Position" in nrn(f, 15)[0]["begruendung"])
    f = pruefe_struktur(tab(zeile("1.1.1", "Boden lösen"), zeile("1.1.2", "Zulage Fels")))
    check("Nr. 15 negativ: Grundposition davor im selben Abschnitt", not nrn(f, 15))
    f = pruefe_struktur(tab(zeile("1.1.1", "Boden lösen"), zeile("1.2.1", "Zul. Fels")))
    check("Nr. 15: Grundposition nur in anderem Abschnitt → Fund", len(nrn(f, 15)) == 1)
    f = pruefe_struktur(tab(zeile("1.1.1", "Zulage A"), zeile("1.1.2", "Zulage B")))
    check("Nr. 15: zwei Zulagen ohne Grundposition → zwei Funde", len(nrn(f, 15)) == 2)
    f = pruefe_struktur(tab(zeile("1.1.1", "Boden lösen"), zeile("1.1.2", "Zulage zu Pos. 1.9.9 Fels")))
    check("Nr. 15: Zulage nennt nicht vorhandene OZ → nachweisbarer Fehler",
          len(nrn(f, 15)) == 1 and nrn(f, 15)[0]["kategorie"] == FEHLER and "1.9.9" in nrn(f, 15)[0]["begruendung"])
    f = pruefe_struktur(tab(zeile("1.1.1", "Zulage zu Position 2.1.1, Fels"), zeile("2.1.1", "Boden lösen")))
    check("Nr. 15 negativ: genannte OZ existiert (auch in anderem Abschnitt)", not nrn(f, 15))
    f = pruefe_struktur(tab(zeile("1.1.1", "Boden"), zeile("1.1.2", "Zulage Fels", lang="zu Pos. 7. 7. 7. ausführen")))
    check("Nr. 15: OZ-Verweis im Langtext („7. 7. 7.“), Ausschnitt als Beleg",
          len(nrn(f, 15)) == 1 and any("7. 7. 7" in b for b in nrn(f, 15)[0]["belege"]))
    # Nr. 16
    gl = dict(kurz="Betonstahl 500 S", lang="liefern, schneiden, biegen und verlegen", einheit="t")
    f = pruefe_struktur(tab(zeile("3.2.100", **gl), zeile("3.2.110", "Anderes"), zeile("3.2.195", **gl)))
    g = nrn(f, 16)
    check("Nr. 16: gleiche Leistung zweimal im Abschnitt → ein Fund mit beiden Positionen",
          len(g) == 1 and [p["oz"] for p in g[0]["positionen"]] == ["3.2.100", "3.2.195"]
          and g[0]["kategorie"] == WIDERSPRUCH)
    check("Nr. 16: Belege = Kurztext und Langtextanfang, Feldbelege OZ und Einheit",
          g and g[0]["belege"] == ["Betonstahl 500 S", "liefern, schneiden, biegen und verlegen"]
          and {"art": "Feldwert", "text": "Einheit: t"} in g[0]["feldbelege"])
    for name, b in [("anderer Abschnitt", zeile("3.3.1", **gl)),
                    ("andere Einheit", zeile("3.2.195", gl["kurz"], gl["lang"], einheit="kg")),
                    ("anderer Langtext", zeile("3.2.195", gl["kurz"], "liefern und verlegen", einheit="t")),
                    ("anderer Titel", zeile("3.2.195", **gl, titel="U"))]:
        check(f"Nr. 16 negativ: {name}", not nrn(pruefe_struktur(tab(zeile("3.2.100", **gl), b)), 16))
    ohne = dict(kurz="Betonstahl 500 S", einheit="t")
    check("Nr. 16 negativ: ohne eigenen Langtext",
          not nrn(pruefe_struktur(tab(zeile("3.2.1", **ohne), zeile("3.2.2", **ohne))), 16))
    wv = dict(kurz="wie vor, jedoch DN 250", lang="wie vor, jedoch DN 250 liefern", einheit="m")
    check("Nr. 16 negativ: Bezugstext „wie vor, jedoch“ (Falle Angebot 3.1.20/3.1.60)",
          not nrn(pruefe_struktur(tab(zeile("3.1.20", **wv), zeile("3.1.60", **wv))), 16))
    vb = dict(kurz="Zulage Entsorgung für vorbeschriebenen Wurzelstock", lang="vorbeschrieben", einheit="St")
    check("Nr. 16 negativ: „vorbeschrieben“ (Falle 501-24-01 02.03.0005/0007)",
          not nrn(pruefe_struktur(tab(zeile("2.3.5", **vb), zeile("2.3.7", **vb))), 16))
    zb = dict(kurz="Schutzrohr für Anbindeleitung", lang="passend zu zuvor beschriebener Anbindeleitung", einheit="m")
    check("Nr. 16 negativ: „zuvor beschriebener“ (LV_14a .5/.30)",
          not nrn(pruefe_struktur(tab(zeile(".5", **zb), zeile(".30", **zb))), 16))
    for art, roh in (("Bedarf", ""), ("Wahl", ""), ("Normal", "Bedarfsposition WithoutTotal")):
        check(f"Nr. 16 negativ: {art or roh}",
              not nrn(pruefe_struktur(tab(zeile("3.2.1", **gl, art=art, art_roh=roh),
                                          zeile("3.2.2", **gl, art=art, art_roh=roh))), 16))
    check("Nr. 16 negativ: „Alternativposition“ im Text",
          not nrn(pruefe_struktur(tab(zeile("3.2.1", gl["kurz"], "Alternativposition zu 3.2.0", einheit="t"),
                                      zeile("3.2.2", gl["kurz"], "Alternativposition zu 3.2.0", einheit="t"))), 16))
    try:
        pruefe_struktur(pd.DataFrame([dict(zeile("1.1", "Zulage"), format="PDF")], columns=COLUMNS))
        check("PDF ohne Quelle: Fehler", False)
    except ValueError:
        check("PDF ohne Quelle: Fehler", True)
    check("reine Preisdatei: keine Funde", pruefe_struktur(tab(zeile("1.1", ""), zeile("1.2", ""))) == [])


# --------------------------------------------------------------------------- 2. echte Dateien

def finde(funde, nr, datei, oz):
    return [f for f in funde if f["pruefung"] == nr and f["positionen"][0]["datei"] == datei
            and normalisiere_oz(f["positionen"][0]["oz"]) == normalisiere_oz(oz)]


def test_echt(cache, alle):
    soll15 = [("501-24-01_GAEB-XML_sas.x83", "03.02.0001"), ("501-24-01_GAEB-XML_sas.x83", "03.02.0002"),
              ("[ORT_024] LV24069.D86", "8.2.1")]
    ist15 = sorted((f["positionen"][0]["datei"], f["positionen"][0]["oz"]) for f in alle if f["pruefung"] == 15)
    check("Nr. 15: genau die 3 Zulagen aus der Vorgabe", ist15 == sorted(soll15), str(ist15))
    zul = Counter()
    for name, df in cache.items():
        if nur_preise(df):
            continue
        for k in df[df.typ == "Position"].kurztext:
            if isinstance(k, str) and ist_zulage(k):
                zul[re.match(r"\s*(\w+\.?)", k).group(1).lower()[:4]] += 1
    print(f"       Zulagen im Datensatz: {sum(zul.values())} {dict(zul)}")
    lv00 = cache["LV_00_Roh_und_Erdauarbeiten.pdf"]
    check("„Zul.“ wird erfasst (LV_00 3.1.270 „Zul.Deckenschalung,SB2“)",
          ist_zulage(lv00[lv00.oz == "3.1.270"].kurztext.iloc[0]))
    f = finde(alle, 16, "LV_00_Roh_und_Erdauarbeiten.pdf", "3.2.100")
    check("Nr. 16: Kandidat LV_00 3.2.100/3.2.195", bool(f) and [p["oz"] for p in f[0]["positionen"]]
          == ["3.2.100", "3.2.195"])
    for datei, oz in (("Angebot AN24-0305.pdf", "3.1.20"), ("Leistungsverzeichnis.pdf", "3.1.20"),
                      ("501-24-01_GAEB-XML_sas.x83", "02.03.0005"), ("LV_00_Roh_und_Erdauarbeiten.pdf", "3.1.270"),
                      ("LV_21_Natursteinarbeiten.pdf", "13.4.20")):
        check(f"Nr. 16 Falle ohne Fund: {datei} {oz}", not finde(alle, 16, datei, oz))
    for name in ("StBALV23040.D84", "Angebot AN24-0305.D84"):
        check(f"nur Preise: {name}", pruefe_struktur(cache[name], D / name) == [])
    check("Datenvertrag: genau die Felder", all(list(f) == FELDER for f in alle))
    check("Stufe 1, Rang laut Vorschlag, Status offen",
          all(f["stufe"] == 1 and f["prioritaet_in_stufe"] == RANG_VORSCHLAG[f["pruefung"]]
              and f["status"] == "offen" for f in alle))
    check("Kostenwirkung je Prüfung", set(KOSTENWIRKUNG) == {15, 16})
    check("Fund-IDs eindeutig", len({f["id"] for f in alle}) == len(alle))
    texte = {(n, normalisiere_oz(r.oz)): (r.kurztext or "", r.langtext or "")
             for n, df in cache.items() for r in df[df.typ == "Position"].itertuples()}
    falsch = [f["id"] for f in alle for p in f["positionen"]
              if not all(beleg_im_text(b, *texte[(p["datei"], normalisiere_oz(p["oz"]))]) for b in f["belege"])]
    check("R5: jeder Beleg in Kurz- oder Langtext jeder Position (parse())", not falsch, str(falsch[:3]))
    check("R7: keine verbotenen Begriffe", not [f for f in alle if VERBOTEN.search(f["titel"] + f["begruendung"])])
    check("Sortierung je Datei", all([f for f in alle if f["positionen"][0]["datei"] == n] ==
                                     sortiere([f for f in alle if f["positionen"][0]["datei"] == n]) for n in cache))


# --------------------------------------------------------------------------- 3./4.

def test_doppellauf(cache, alle):
    namen = sorted(cache)
    b = {n: pruefe_struktur(cache[n], D / n) for n in reversed(namen)}
    zweit = [f for n in namen for f in b[n]]
    check("Doppellauf (E14): byte-gleich, zweiter Lauf in umgekehrter Reihenfolge",
          json.dumps(alle, ensure_ascii=False) == json.dumps(zweit, ensure_ascii=False))


def test_skeptiker(alle):
    roh, erg = {}, []
    for f in alle:
        for p in f["positionen"]:
            pfad = D / p["datei"]
            e = pfad.suffix.lower()
            if p["datei"] not in roh:
                roh[p["datei"]] = (original_xml(pfad) if e.startswith(".x") else
                                   original_gaeb90(pfad)[0] if e.startswith(".d") else PdfOriginal(pfad))
            o = roh[p["datei"]]
            if isinstance(o, PdfOriginal):
                stellen = [o.finde(b, p["seite"] or 1) for b in f["belege"]]
                fehlt = [b for b, s in zip(f["belege"], stellen) if s is None]
                stelle = "S. " + ", ".join(sorted({str(s) for s in stellen if s}))
            else:
                k = normalisiere_oz(p["oz"]) if e.startswith(".x") else p["oz"].replace(".", "")
                x = o.get(k)
                fehlt = ["Position fehlt"] if x is None else [b for b in f["belege"] if b not in x[1]]
                stelle = None if x is None else (f"Item {x[0]}" if e.startswith(".x") else f"Satz 21 Z. {x[0]}")
            erg.append({"id": f["id"], "datei": p["datei"], "oz": p["oz"], "stelle": stelle, "fehlt": fehlt})
    print("       Skeptiker:", [(e["id"], e["oz"], e["stelle"], "gefunden" if not e["fehlt"] else e["fehlt"])
                                for e in erg])
    check("Skeptiker: jeder Beleg jeder Position im Original", all(not e["fehlt"] for e in erg))
    check("Skeptiker: mindestens 5 Positionen oder alle geprüft", len(erg) >= min(5, sum(len(f["positionen"])
                                                                                        for f in alle)))
    return erg


if __name__ == "__main__":
    test_klein()
    cache = {p.name: parse(str(p)) for p in sorted(D.iterdir())
             if not p.name.startswith(".") and p.suffix.lower() != ".docx"}
    alle = [f for n in sorted(cache) for f in pruefe_struktur(cache[n], D / n)]
    print(f"       {len(alle)} Funde: " + str(dict(Counter(f['pruefung'] for f in alle))))
    test_echt(cache, alle)
    test_doppellauf(cache, alle)
    erg = test_skeptiker(alle)
    if BERICHT:
        ziel = Path(BERICHT).resolve()
        if ziel.is_relative_to(D.resolve()) or ziel.is_relative_to(Path("data").resolve()) \
                or ziel.is_relative_to(Path("../data").resolve()):
            sys.exit("--bericht nie in data/ (E12 (4))")
        ziel.write_text(json.dumps({"funde": alle, "skeptiker": erg}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
