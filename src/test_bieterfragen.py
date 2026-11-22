"""
test_bieterfragen.py - Tests für src/bieterfragen.py (Backlog B3, Sitzung B2). Export nur in einen Temp-Ordner.
  1. kleine Funde: Vorlage je Prüfung, Auswahl (Rückfrage, nicht verworfen), Reihenfolge, R7
  2. echte Funde: Nr. 1–4 (alle_pruefungen) und Nr. 15/16 (pruefe_struktur) aus Dateien des Datensatzes; jede Frage
     enthält jeden Beleg wörtlich; Belege stehen in Kurz- oder Langtext der Position (R5)
  3. xlsx: Blätter, Überschriften, Legende, Doppellauf gleich
Aufruf aus src/:  python test_bieterfragen.py <data/raw>
"""
import io
import re
import sys
import tempfile
from pathlib import Path

from openpyxl import load_workbook

from lv_parser import parse
from pruefung_widerspruch import normalisiere_oz, beleg_im_text
from pruefung_formal import alle_pruefungen
from pruefung_struktur import pruefe_struktur
from bieterfragen import (bieterfragen, frage, schreibe_xlsx, SPALTEN, HINWEIS, empfehlung, ausgenommen,
                          HINWEIS_AUFTRAG, xlsx_bytes)

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
VERBOTEN = re.compile(r"Anspruch|berechtigt|durchsetzbar|§|Nachtrag|Vertrag", re.I)
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fund(nr, oz, belege, status="offen", datei="a.X83", kategorie="Unklarheit", titel="T", begruendung=""):
    return {"id": f"{nr}|{datei}|{oz}", "pruefung": nr, "kategorie": kategorie, "titel": titel,
            "positionen": [{"datei": datei, "oz": o, "seite": None} for o in oz.split("+")], "belege": belege,
            "feldbelege": [], "begruendung": begruendung, "status": status}


def test_klein():
    f1 = fund(1, "5.1.4", ["Edelstahl-Rohr DN 125", "Edelstahlrohr DN 100, bis PN 16"])
    check("Nr. 1: Frage nennt beide Belege und fragt nach der Nennweite",
          frage(f1) == "Pos. 5.1.4: Im Kurztext steht „Edelstahl-Rohr DN 125“, im Langtext „Edelstahlrohr DN 100, "
                       "bis PN 16“. Welche Nennweite ist auszuführen?")
    f16 = fund(16, "3.2.100+3.2.195", ["Betonstahl 500 S"])
    check("Nr. 16: beide OZ", "Pos. 3.2.100, 3.2.195 beschreiben dieselbe Leistung" in frage(f16))
    f4 = fund(4, "1.1+1.1", ["Leitung spülen", "Leitung prüfen"])
    check("Nr. 4: OZ mehrfach", frage(f4).startswith("Die OZ 1.1 ist im LV 2-mal vergeben"))
    f15f = fund(15, "1.2", ["Zulage zu Pos. 9.9"], kategorie="nachweisbarer Fehler")
    check("Nr. 15 (Fehler) und (Unklarheit) mit verschiedener Frage",
          "nicht vor" in frage(f15f) and "Auf welche Position" in frage(fund(15, "1.2", ["Zulage Fels"])))
    rest = [fund(7, "2.1", ["oder gleichwertig"]), fund(2, "1.1", ["C25/30", "C30/37"], status="verworfen"),
            fund(3, "1.10", ["Boden"], datei="b.X83"), fund(3, "1.9", ["Boden"], datei="b.X83"), f1,
            fund(19, "4.1", ["Asphalt"], begruendung="… Empfehlung: vormerken."),
            fund(99, "4.2", ["X"], begruendung="… Empfehlung laut Prüfkatalog: Rückfrage stellen.")]
    z = bieterfragen(rest)
    check("Auswahl: nur Rückfrage-Prüfungen (Nr. 7, 19 nicht), verworfen fällt weg, Empfehlung im Text zählt",
          [r["Fund-ID"] for r in z] == ["99|a.X83|4.2", "1|a.X83|5.1.4", "3|b.X83|1.9", "3|b.X83|1.10"],
          str([r["Fund-ID"] for r in z]))
    check("laufende Nummer 1…n, Spalten vollständig", [r["Nr."] for r in z] == [1, 2, 3, 4]
          and all(list(r) == SPALTEN for r in z))
    # FS-B2-11: Auswahl nach der Empfehlung des einzelnen Funds, Auftrags-LV ohne Fragen
    n3v = fund(3, "8.1.1", ["KSB Etabloc"], begruendung="Position im Auftrags-LV ohne Menge und Einheit – "
                                                         "Abrechnungsgrundlage klären. Empfehlung laut Prüfkatalog: vormerken.")
    n3r = fund(3, "1.3", ["Boden"], begruendung="Das Feld Menge ist leer. Empfehlung laut Prüfkatalog: klärende Rückfrage.")
    check("Empfehlung je Fund: Nr. 3 „vormerken“ → keine Frage, Nr. 3 „klärende Rückfrage“ → Frage",
          [r["Fund-ID"] for r in bieterfragen([n3v, n3r])] == ["3|a.X83|1.3"]
          and empfehlung(n3v) == ("vormerken", "Fund"))
    check("Feld `empfehlung` hat Vorrang vor Begründung und Katalog",
          bieterfragen([dict(f1, empfehlung="nur Hinweis")]) == [] and empfehlung(f1) == ("klärende Rückfrage", "Katalog"))
    d86 = [fund(3, "8.1.1", ["KSB"], datei="[ORT_024] LV24069.D86",
                begruendung="Empfehlung laut Prüfkatalog: klärende Rückfrage."),
           fund(16, "1.1+1.2", ["Rinne"], datei="StBALV23040.D86")]
    check("Auftrags-LV (.D86): keine Bieterfragen, Hinweis je Datei",
          bieterfragen(d86) == [] and ausgenommen(d86) == [("StBALV23040.D86", HINWEIS_AUFTRAG),
                                                            ("[ORT_024] LV24069.D86", HINWEIS_AUFTRAG)])
    alle = [f1, f16, f4, f15f, fund(3, "1", ["x"]), fund(17, "1", ["x"]), fund(2, "1", ["a", "b"])]
    check("R7: keine Rechts- oder Nachtragsbegriffe in den Fragen", not [frage(f) for f in alle if VERBOTEN.search(frage(f))])


def test_echt(tmp):
    funde = []
    for name in ("8209.003_Leistungsverzeichnis_leer.X83", "LV_00_Roh_und_Erdauarbeiten.pdf",
                 "501-24-01_GAEB-XML_sas.x83", "[ORT_024] LV24069.D86"):
        df = parse(str(D / name))
        f16 = alle_pruefungen(df, D / name)
        funde += f16 + pruefe_struktur(df, D / name, f16)
        # R5 laut Datenvertrag: Kurz- oder Langtext, bei PDF auch der Vermerk aus art_roh (Nr. 5)
        texte = {normalisiere_oz(r.oz): (r.kurztext or "", r.langtext or "", r.art_roh if isinstance(r.art_roh, str) else "")
                 for r in df[df.typ == "Position"].itertuples()}
        for f in f16 + pruefe_struktur(df, D / name, f16):
            for p in f["positionen"]:
                if not all(beleg_im_text(b, *texte[normalisiere_oz(p["oz"])]) for b in f["belege"]):
                    check(f"R5 {f['id']}", False)
    z = bieterfragen(funde)
    nrn = sorted({int(r["Prüfung"].split()[1]) for r in z})
    print(f"       {len(z)} Bieterfragen aus {len(funde)} Funden; Prüfungen {nrn}")
    for r in z[:4]:
        print(f"       {r['Nr.']} {r['Datei']} {r['OZ']}: {r['Frage (Entwurf)'][:110]}")
    check("echte Funde: Fragen zu Nr. 1, 15 und 16 entstehen", {1, 15, 16} <= set(nrn), str(nrn))
    f_by = {f["id"]: f for f in funde}
    check("jeder Beleg steht wörtlich in Frage oder Beleg-Spalte",
          all(all(b in r["Beleg (wörtlich aus dem LV)"] for b in f_by[r["Fund-ID"]]["belege"]) for r in z))
    check("R7 bei echten Fragen", not [r for r in z if VERBOTEN.search(r["Frage (Entwurf)"])])
    z86 = [r for r in z if r["Datei"].lower().endswith(".d86")]
    check("echte Daten: [ORT_024] LV24069.D86 (Auftrags-LV) ohne Bieterfragen, mit Hinweis",
          not z86 and ("[ORT_024] LV24069.D86", HINWEIS_AUFTRAG) in ausgenommen(funde))
    check("echte Daten: keine Frage zu einem Fund mit „vormerken“",
          all(empfehlung(f_by[r["Fund-ID"]])[0].lower() != "vormerken" for r in z))
    p1 = schreibe_xlsx(z, tmp / "a.xlsx", ausgenommen(funde))
    p2 = schreibe_xlsx(bieterfragen(list(reversed(funde))), tmp / "b.xlsx", ausgenommen(list(reversed(funde))))
    lies = lambda p: [[c.value for c in row] for ws in load_workbook(p) for row in ws.iter_rows()]
    check("Doppellauf: gleicher Inhalt, auch bei umgekehrter Fundreihenfolge (E14)", lies(p1) == lies(p2))
    wb = load_workbook(p1)
    check("Blätter Bieterfragen und Legende, Hinweis in Zeile 1, Überschriften in Zeile 2",
          wb.sheetnames == ["Bieterfragen", "Legende"] and wb["Bieterfragen"]["A1"].value == HINWEIS
          and [c.value for c in wb["Bieterfragen"][2]] == SPALTEN)
    check("xlsx_bytes liefert dieselbe Tabelle wie schreibe_xlsx",
          lies(p1) == [[c.value for c in row] for ws in load_workbook(io.BytesIO(
              xlsx_bytes(z, ausgenommen(funde)))) for row in ws.iter_rows()])
    check("Legende erklärt jede Spalte", [r[0].value for r in wb["Legende"].iter_rows(min_row=2)] == SPALTEN)
    check("kein Dateipfad („data/“) in Zellen", not any("data/" in str(v) for row in lies(p1) for v in row if v))
    boese = bieterfragen([fund(3, "1.1", ["=HYPERLINK(\"http://x\",\"y\")"], datei="+cmd.X83"),
                          fund(3, "1.2", ["@SUMME(A1)", "-1+1", "Steuer\x07zeichen"])])
    wb2 = load_workbook(schreibe_xlsx(boese, tmp / "c.xlsx"))
    zellen = [c for row in wb2["Bieterfragen"].iter_rows(min_row=3) for c in row if isinstance(c.value, str)]
    check("Formel-Einschleusen: Zellen mit =, +, @, - bleiben Text und wörtlich; Steuerzeichen → Leerzeichen",
          all(c.data_type == "s" for c in zellen) and "=HYPERLINK(\"http://x\",\"y\")" in [c.value for c in zellen]
          and "+cmd.X83" in [c.value for c in zellen] and any("Steuer zeichen" in c.value for c in zellen))
    try:
        schreibe_xlsx(z, Path(__file__).resolve().parents[1] / "data" / "findings" / "x.xlsx")
        check("Schreiben in data/ abgelehnt", False)
    except ValueError:
        check("Schreiben in data/ abgelehnt", True)


if __name__ == "__main__":
    test_klein()
    with tempfile.TemporaryDirectory() as t:
        test_echt(Path(t))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
