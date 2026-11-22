"""
test_skeptiker_s2.py - Tests für src/skeptiker_s2.py (Lücke L57, Team 22.11.2026, F2).

Teil 1 mit erfundenen Zeilen, Teil 2 am Original in data/raw (nur lesen). Schreibt nichts in data/.
Aufruf aus der Projektwurzel (uv-Befehl siehe AGENTS.md):
  python src/test_skeptiker_s2.py data/raw
Exit-Code 0 = alle Tests bestanden.
"""
import ast
import copy
import inspect
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skeptiker_s2 as S                                              # noqa: E402
from bericht import beleg_pruefung, lade_s2                           # noqa: E402

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
ergebnisse = []
Z = [(1, "    1.1      Rohr DN 100 (erfunden)"), (1, "             Langtext der ersten Position"),
     (1, "                         2,000 St ......................... ........................."),
     (1, "             Vorbemerkung des nächsten Bereichs"), (1, "    1.2      Schieber (erfunden)"),
     (1, "             Langtext der zweiten Position"), (2, "                         1,000    ......................... ........................."),
     (2, "             Unterbeschreibung 1:"), (2, "             Zubehör der zweiten Position"),
     (2, "             Gemäß Leitbeschreibung 1:"), (2, "    1.3      Baustelle (erfunden)"),
     (2, "             Baustelle einrichten"), (2, "                         1,000 pau ......................... .........................")]


def check(name, ok, detail=""):
    ok = bool(ok)
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fund(oz, belege, feld=(), nr=7):
    oz = [oz] if isinstance(oz, str) else oz
    return {"id": f"{nr}|x.pdf|{oz[0]}", "pruefung": nr, "positionen": [{"datei": "x.pdf", "oz": o, "seite": 1} for o in oz],
            "belege": list(belege), "feldbelege": [{"art": "Feldwert", "text": t} for t in feld]}


def bestanden(f, zeilen=Z):
    return S.pruefe_fund(f, zeilen)["ergebnis"] == S.BESTANDEN


def test_regeln():
    check("Mengenzeile mit Einheit", S.mengenzeile(Z[2][1]) == ("2,000", "St"))
    check("Mengenzeile ohne Einheit", S.mengenzeile(Z[6][1]) == ("1,000", ""))
    check("Mengenzeile mit Einheit pau", S.mengenzeile(Z[12][1]) == ("1,000", "pau"))
    check("Textzeile ist keine Mengenzeile", S.mengenzeile("Gewicht ca. 55 kg") is None)
    check("Positiv: Beleg im Block der Position", bestanden(fund("1.1", ["Rohr DN 100 (erfunden)", "Langtext der ersten Position"])))
    check("Leerraum im Beleg zählt nicht", bestanden(fund("1.1", ["Langtext   der\nersten Position"])))
    check("Negativ: Beleg hinter der Mengenzeile", not bestanden(fund("1.1", ["Vorbemerkung des nächsten Bereichs"])))
    check("Negativ: Beleg aus der Folgeposition", not bestanden(fund("1.1", ["Langtext der zweiten Position"])))
    check("Negativ: abgewandelter Beleg", not bestanden(fund("1.1", ["Langtext der 1. Position"])))
    check("Negativ: Position nicht im Original", not bestanden(fund("9.9", ["Rohr"])))
    check("Unterbeschreibung gehört zur Position", bestanden(fund("1.2", ["Zubehör der zweiten Position"])))
    check("Einleitung der Folgeposition gehört nicht dazu", not bestanden(fund("1.2", ["Gemäß Leitbeschreibung 1:"])))
    check("Feldwert Einheit stimmt", bestanden(fund("1.3", ["Baustelle einrichten"], ["Einheit: pau"], 6)))
    check("Negativ: Feldwert Einheit falsch", not bestanden(fund("1.3", ["Baustelle einrichten"], ["Einheit: psch"], 6)))
    check("Feldwert „Einheit: (leer)“ stimmt", bestanden(fund("1.2", ["Schieber (erfunden)"], ["Einheit: (leer)"], 3)))
    check("Negativ: „Einheit: (leer)“ bei gedruckter Einheit", not bestanden(fund("1.1", ["Rohr DN 100 (erfunden)"], ["Einheit: (leer)"], 3)))
    check("Negativ: nicht prüfbarer Feldwert wird nicht bestanden", not bestanden(fund("1.1", ["Rohr DN 100 (erfunden)"], ["Unbekannt: 2"])))
    check("Zwei Positionen: Beleg muss in beiden stehen", not bestanden(fund(["1.1", "1.2"], ["Rohr DN 100 (erfunden)"], ["OZ: 1.1", "OZ: 1.2"], 16)))
    check("Negativ: fremde OZ als Feldwert", not bestanden(fund("1.1", ["Rohr DN 100 (erfunden)"], ["OZ: 7.7"], 16)))


XML = """<?xml version="1.0" encoding="UTF-8"?><GAEB xmlns="http://www.gaeb.de/GAEB_DA_XML/DA83/3.3"><BoQ><BoQBody>
<BoQCtgy RNoPart="01"><BoQBody><Itemlist>
<Item RNoPart="0001" ID="A"><Qty>2.000</Qty><QU>St</QU><Provis>WithoutTotal</Provis><Description><CompleteText><DetailTxt><Text><p><span>Langtext </span><span>der ersten</span></p><p>Position</p></Text></DetailTxt><OutlineText><OutlTxt><TextOutlTxt><p><span>Rohr DN 100</span></p></TextOutlTxt></OutlTxt></OutlineText></CompleteText></Description><SubDescr><SubDNo>1</SubDNo><Description><CompleteText><DetailTxt><Text><p><span>Zubehoer eins</span></p></Text></DetailTxt></CompleteText></Description></SubDescr></Item>
<Item RNoPart="0002" ID="B"><Qty>0.000</Qty><QU>psch</QU><Description><CompleteText><DetailTxt><Text><p><span>Text der zweiten</span></p></Text></DetailTxt></CompleteText></Description></Item>
</Itemlist></BoQBody></BoQCtgy></BoQBody></BoQ></GAEB>"""
G90 = ["20" + "Vorbemerkung vor der Position".ljust(70), "21" + "010001".ljust(21) + "00000002000" + "St  ",
       "25" + "Rohr DN 100".ljust(70), "26" + "Langtext der".ljust(70), "26" + "ersten Position".ljust(70),
       "20" + "Vorbemerkung hinter der Position".ljust(70), "26" + "fremder Text".ljust(70),
       "21" + "010002".ljust(21) + "00000000000" + "psch", "25" + "Schieber".ljust(70)]


def test_formate():
    z = [(1, "    1.1      Rohr (erfunden)"), (1, "             erste Zeile"), (2, "    1        Titel Anlage"),
         (2, "    1.0      Bereich Anlage"), (2, "             zweite Zeile"),
         (2, "                         2,000 St ......................... .........................")]
    kopf = [(1, "    1        Titel Anlage"), (1, "    1.0      Bereich Anlage")] + z[:2] + z[2:]
    check("PDF: wiederkehrende Kopfzeile beendet die Position nicht und zählt nicht als Text",
          bestanden(fund("1.1", ["erste Zeile zweite Zeile"], ["Einheit: St"]), kopf))
    a = [(1, "    1.1      Text A"), (1, "                         1,000 St ...... ......"), (2, "    1.2      Text B"),
         (2, "                         1,000 St ...... ......")]
    check("PDF: neue OZ beendet die Position weiterhin", not bestanden(fund("1.1", ["Text B"]), a))
    inl = [(1, "    1.1      2,000 St 10,00 20,00"), (1, "             Kurztext Angebot"), (1, "    Fusszeile"),
           (1, "    1.2      1,000 St 10,00 10,00")]
    check("PDF: Menge in der OZ-Zeile (Angebot), eingerückter Text ist Beleg",
          bestanden(fund("1.1", ["Kurztext Angebot"], ["Einheit: St", "Menge: 2"]), inl))
    check("PDF, negativ: Fußzeile im Angebots-Layout gehört nicht dazu", not bestanden(fund("1.1", ["Fusszeile"]), inl))
    with tempfile.TemporaryDirectory() as tmp:
        x = Path(tmp) / "t.X83"
        x.write_text(XML, encoding="utf-8")
        o = S.lies_original(x)
        ok = lambda oz, b, fw=(): S.pruefe_fund_format(fund(oz, b, fw), o)["ergebnis"] == S.BESTANDEN
        check("XML: Kurz- und Langtext wörtlich, Span ohne Zusatz-Leerzeichen", ok("01.0001", ["Rohr DN 100", "Langtext der ersten Position"]))
        check("XML: Unterbeschreibung gehört zur Position", ok("1.1", ["Zubehoer eins"]))
        check("XML: Einheit, Menge und Provis am Original", ok("01.0001", ["Rohr DN 100"], ["Einheit: St", "Menge: 2", "<Provis>WithoutTotal</Provis>"]))
        check("XML, negativ: Beleg aus anderem Item", not ok("01.0001", ["Text der zweiten"]))
        check("XML, negativ: falsche Einheit", not ok("01.0001", ["Rohr DN 100"], ["Einheit: m"]))
        check("XML, negativ: falsche Menge", not ok("01.0001", ["Rohr DN 100"], ["Menge: 0"]))
        check("XML, negativ: Provis fehlt", not ok("01.0002", ["Text der zweiten"], ["<Provis>WithoutTotal</Provis>"]))
        check("XML: Menge 0 am Original", ok("01.0002", ["Text der zweiten"], ["Menge: 0", "Einheit: psch"]))
        g = Path(tmp) / "t.D83"
        g.write_bytes(("\r\n".join(G90) + "\r\n").encode("cp850"))
        o = S.lies_original(g)
        check("GAEB 90: Satz 25/26 über Zeilen, Menge und Einheit aus Satz 21",
              ok("01.0001", ["Rohr DN 100", "Langtext der ersten Position"], ["Einheit: St", "Menge: 2"]))
        check("GAEB 90, negativ: Text hinter dem Block (nach Satz 20) gehört nicht dazu", not ok("01.0001", ["fremder Text"]))
        check("GAEB 90, negativ: Vorbemerkung", not ok("01.0001", ["Vorbemerkung hinter der Position"]))
        check("GAEB 90: Menge 0", ok("01.0002", ["Schieber"], ["Menge: 0", "Einheit: psch"]))
        check("GAEB 90, negativ: Position fehlt", not ok("09.0009", ["Rohr"]))
    r = [dict(fund("9.1", ["x"], nr=n), stufe=s) for n, s in ((9, 3), (3, 1), (2, 1), (6, 2), (1, 1), (11, 4))]
    check("Reihenfolge: Stufe 1 mit Nr. 1 und 2 zuerst, dann 2, 3, 4",
          [f["pruefung"] for f in sorted(r, key=S.reihenfolge)] == [1, 2, 3, 6, 9, 11])


def test_ergaenzen():
    alt = {"id": "9|alt.pdf|1", "belege": [{"text": "alt"}], "feldbelege": [], "ergebnis": S.BESTANDEN, "fundstelle": "S. 1"}
    geaendert = {"id": "7|x.pdf|1.2", "belege": [{"text": "Schieber (erfunden)"}, {"text": "früher"}], "feldbelege": [],
                 "ergebnis": S.BESTANDEN}
    doc = {"stand": "t", "funde": [alt, geaendert]}
    vorher = copy.deepcopy(doc)
    gut, schlecht, f3 = fund("1.1", ["Rohr DN 100 (erfunden)"]), fund("1.3", ["nicht im Original"]), fund("1.2", ["Schieber (erfunden)"])
    funde = [gut, schlecht, f3]
    erg = [S.pruefe_fund(f, Z) for f in funde]
    neu, n, e = S.ergaenze(doc, funde, erg)
    ids = [x["id"] for x in neu["funde"]]
    check("Nur bestandene Einträge werden ergänzt", n == 1 and gut["id"] in ids and schlecht["id"] not in ids, str(ids))
    check("Geänderte Belege eines Ziel-Funds werden ersetzt", e == 1 and [b["text"] for b in neu["funde"][1]["belege"]] == ["Schieber (erfunden)"])
    check("Fremde Einträge bleiben unverändert", neu["funde"][0] == alt)
    check("Eingabe wird nicht verändert", doc == vorher)
    ohne = {k: v for k, v in gut.items() if k != "feldbelege"}
    check("Fund ohne Feld „feldbelege“ (Nr. 1/2): Eintrag ohne dieses Feld", "feldbelege" not in S.eintrag(ohne, erg[0]))
    check("Fund mit Feld „feldbelege“: Eintrag mit diesem Feld", "feldbelege" in S.eintrag(gut, erg[0]))
    zweit, n2, e2 = S.ergaenze(neu, funde, erg)
    check("Zweiter Lauf ändert nichts", (n2, e2) == (0, 0) and zweit == neu)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "s2.json"
        S.schreibe(neu, p)
        check("Schreibt gültiges JSON", json.loads(p.read_text(encoding="utf-8")) == neu)
    try:
        S.schreibe(neu, S.ROOT / "data" / "raw" / "x.json")
        check("Schreiben nach data/raw wird abgelehnt", False)
    except ValueError:
        check("Schreiben nach data/raw wird abgelehnt", True)


def test_ohne_parse():
    code = "".join(inspect.getsource(x) for x in (S.seitenzeilen, S.ohne_kopf_fuss, S.block, S.pruefe_fund, S.mengenzeile,
                                                   S.original_xml, S.original_gaeb90, S.lies_original, S.pruefe_fund_format, S._bewerte))
    baum = ast.parse(code)                     # Aufrufe statt Text: Docstrings dürfen „ohne parse()“ nennen
    aufrufe = {n.func.id for n in ast.walk(baum) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    importe = {a.name for n in ast.walk(baum) if isinstance(n, ast.Import) for a in n.names}
    importe |= {n.module for n in ast.walk(baum) if isinstance(n, ast.ImportFrom)}
    check("Belegprüfung nutzt weder parse() noch den Parser", "parse" not in aufrufe and "lv_parser" not in importe,
          str(sorted(aufrufe & {"parse"})))
    kopf = inspect.getsource(S).split("def zusammen")[0]
    check("Modul importiert den Parser nicht beim Laden", "import lv_parser" not in kopf and "from lv_parser" not in kopf)


def test_original():
    if not D.is_dir():
        check(f"Ordner {D} vorhanden", False)
        return
    funde = S.lade_funde(D)
    check("Alle 31 Ziel-Funde gibt es", len(funde) == 31 and {f["id"] for f in funde} == set(S.ziel_ids()), str(len(funde)))
    original = {}
    for f in funde:
        original.setdefault(f["positionen"][0]["datei"], S.seitenzeilen(D / f["positionen"][0]["datei"]))
    erg = [S.pruefe_fund(f, original[f["positionen"][0]["datei"]]) for f in funde]
    falsch = [(r["id"], r["fehlt"][:1]) for r in erg if r["ergebnis"] != S.BESTANDEN]
    check("Original: alle 31 Funde bestanden", not falsch, str(falsch[:3]))
    h = next(f for f in funde if f["id"] == "7|HEM2301-2_Gesamt-LV.pdf|6.4.1")
    falsch_h = dict(h, belege=h["belege"] + ["(VAG RETO-STOP oder gleichwertig)"])
    check("Original, negativ: Text hinter der Mengenzeile von HEM 06.04.1 (S. 128) besteht nicht",
          not bestanden(falsch_h, original["HEM2301-2_Gesamt-LV.pdf"]))
    wurzel = Path(__file__).resolve().parent.parent
    # Öffentliches Abgabe-Repo (Team 22.11.2026): Datei fehlt dort bewusst und steht in .gitignore. Im Arbeits-Repo bleibt Fehlen ein Fehler.
    if not S.S2.exists() and "data/qa/s2_ergebnis.json" in (wurzel / ".gitignore").read_text(encoding="utf-8"):
        print("ÜBERSPRUNGEN App-Anzeige „geprüft“: data/qa/s2_ergebnis.json ist im Abgabe-Repo bewusst nicht enthalten")
        return
    s2 = lade_s2()[0]
    offen = [f["id"] for f in funde if beleg_pruefung(f, s2) != "geprüft"]
    check("App zeigt alle 31 Funde als „geprüft“", not offen, str(offen[:3]))


def main():
    test_regeln()
    test_formate()
    test_ergaenzen()
    test_ohne_parse()
    test_original()
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    return 0 if all(ergebnisse) else 1


if __name__ == "__main__":
    sys.exit(main())
