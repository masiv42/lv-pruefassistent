"""
test_ui_positionen.py - Tests für src/pages/2_Positionen.py (Sitzung UI). AppTest im Prozess, erfundene Daten, kein Port.
Mit Pfad zu data/raw zusätzlich ein Durchlauf über alle Dateien (nur lesen):  python test_ui_positionen.py ../data/raw
"""
import importlib.util
import re
import sys
import tempfile
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parent))
SEITE = Path(__file__).with_name("pages") / "2_Positionen.py"
_spec = importlib.util.spec_from_file_location("seite_positionen", SEITE)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(bool(ok))
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def zeile(oz, titel, kurz, lang="", menge=1.0, einheit="m", ep=None, gp=None, seite=None):
    return {"oz": oz, "titel": titel, "kurztext": kurz, "langtext": lang, "menge": menge, "einheit": einheit,
            "ep": ep, "gp": gp, "seite": seite}


def fund(nr, stufe, ozs, kat="Risikohinweis", beleg="Beleg"):
    return {"id": f"{nr}|demo.X83|{ozs[0]}", "pruefung": nr, "kategorie": kat, "titel": f"Prüfung {nr}",
            "positionen": [{"datei": "demo.X83", "oz": o, "seite": None} for o in ozs], "belege": [beleg],
            "feldbelege": [{"art": "Feldwert", "text": "Einheit: psch"}], "begruendung": "Begründung", "stufe": stufe,
            "stufe_begruendung": "s", "prioritaet_in_stufe": 1, "rueckfrage": None, "status": "offen"}


ZEILEN = [zeile("1.10", "Erdbau", "Aushub Baugrube", "Boden lösen", 120.0, "m³", 12.5, 1500.0),
          zeile("1.2", "Erdbau", "Verfüllen", "", 30.0, "m³"),
          zeile("2.1", "Beton", "Stützwand C30/37", "Beton C25/30", 40.0, "m²", 100.0, 4000.0),
          zeile("2.2", "Beton", "Schalung", "wie vor", None, "", None, None),
          zeile("2.3", "Beton", "Bewehrung", "", 2.0, "t")]
FUNDE = [fund(2, 1, ["2.1"], "möglicher Widerspruch", "Stützwand C30/37"), fund(6, 2, ["1.10"]),
         fund(16, 1, ["1.2", "2.3"], "möglicher Widerspruch"), fund(12, 4, ["2.1"], "Unklarheit")]
UEBERSICHT = {"lv_name": "demo.X83", "format": "GAEB XML", "positionen": len(ZEILEN), "nur_preise": False,
              "abdeckung": [], "funde": FUNDE, "kurztexte": {}, "gp": {}, "ki_aktiv": False}
POSITIONEN = {"lv_name": "demo.X83", "format": "GAEB XML", "zeilen": ZEILEN, "daten": b""}


def lauf(uebersicht=UEBERSICHT, positionen=POSITIONEN):
    at = AppTest.from_file(str(SEITE))
    if uebersicht is not None:
        at.session_state["lv_uebersicht"] = uebersicht
    if positionen is not None:
        at.session_state["lv_positionen"] = positionen
    return at.run(timeout=60)


def alle_texte(at):
    t = [m.value for m in at.markdown] + [c.value for c in at.caption] + [x.value for x in at.info] + \
        [x.value for x in at.warning] + [h.value for h in at.title] + [h.value for h in at.subheader] + \
        [x.proto.body for x in at.get("html")]
    return " ".join(str(x) for x in t)


def tabelle_oz(at):
    return list(at.dataframe[0].value["OZ"])


if __name__ == "__main__":
    z = P.zuordnen(ZEILEN, FUNDE)
    check("Menge der Fund-IDs = Fundzahl", P.fund_ids(z) == {f["id"] for f in FUNDE})
    check("Fund mit zwei Positionen steht bei beiden",
          [len(x["funde"]) for x in z] == [1, 1, 2, 0, 1], str([len(x["funde"]) for x in z]))
    check("Spaltensumme = Fundzahl + Mehrfachnennungen", sum(len(x["funde"]) for x in z) == len(FUNDE) + 1)
    check("Höchste Stufe = kleinste Stufennummer", z[2]["hoechste_stufe"] == 1 and z[3]["hoechste_stufe"] is None)
    d = P.zuordnen(ZEILEN + [zeile("2.1", "Beton", "Doppelte OZ")], FUNDE)
    check("Doppelte OZ: Fund an jeder Zeile, zählt einmal", len(d[5]["funde"]) == 2 and P.fund_ids(d) == P.fund_ids(z))
    check("Suche über Langtext, ohne Groß/Klein", [x["oz"] for x in P.filtere(z, "c25/30")] == ["2.1"])
    check("Suche mit zwei Wörtern", [x["oz"] for x in P.filtere(z, "beton schalung")] == ["2.2"])
    check("Filter Titel", len(P.filtere(z, titel=["Erdbau"])) == 2)
    check("Filter Stufe nach irgendeinem Fund der Position",
          [x["oz"] for x in P.filtere(z, stufen=[4])] == ["2.1"])
    check("Filter nur mit Fund", len(P.filtere(z, nur_mit_fund=True)) == 4)
    check("OZ numerisch sortiert", [x["oz"] for x in P.sortierte(z)] == ["1.2", "1.10", "2.1", "2.2", "2.3"])
    check("Sortierung Stufe: ohne Fund zuletzt", P.sortierte(z, "Höchste Stufe")[-1]["oz"] == "2.2")
    check("Sortierung GP: leer zuletzt, nie als 0",
          [x["oz"] for x in P.sortierte(z, "GP laut LV")][:2] == ["2.1", "1.10"])
    t = P.tabelle(z)
    check("Spalten laut Auftrag", list(t.columns) == ["OZ", "Titel", "Kurztext", "Menge", "Einheit", "EP", "GP", "Funde",
                                                      "Höchste Stufe"])
    check("Fehlender Preis bleibt leer", t.loc[1, "EP"] is not None and str(t.loc[1, "EP"]) == "<NA>")
    check("Stufe mit Namen", t.loc[2, "Höchste Stufe"] == "1 – Fehlerprüfung")
    check("Zahl in deutscher Schreibweise", P._de(1234.5, 2) == "1.234,50" and P._de(None, 2) == "–")

    at = lauf(None, None)
    check("ohne LV: Hinweis statt Ausnahme", not at.exception and "Noch kein LV geprüft" in alle_texte(at))
    at = lauf(UEBERSICHT, None)
    check("ohne Positionsdaten: klarer Hinweis", not at.exception and "Positionsdaten" in alle_texte(at))
    at = lauf(UEBERSICHT, dict(POSITIONEN, lv_name="anderes.X83"))
    check("Positionsdaten eines anderen LV werden nicht gezeigt", "Positionsdaten" in alle_texte(at)
          and not len(at.dataframe))

    at = lauf()
    check("Seite ohne Ausnahme", not at.exception, str(at.exception))
    check("Alle Positionen in der Tabelle", tabelle_oz(at) == ["1.2", "1.10", "2.1", "2.2", "2.3"], str(tabelle_oz(at)))
    check("Spalte Funde: Summe = Fundzahl + Mehrfachnennung", int(at.dataframe[0].value["Funde"].sum()) == len(FUNDE) + 1)
    text = alle_texte(at)
    check("Kennzeichnung Parser", P.KENNZEICHNUNG in text)
    check("Fundzahl in der Kachel", ">Funde</dt><dd class=\"lv-kennzahl-wert\">4<" in text)
    check("Mehrfachnennung erklärt", "1 Funde betreffen mehrere Positionen" in text)
    check("Kein Dateipfad", not re.search(r"/Users|data/raw|[A-Z]:\\", text))
    check("Keine verbotenen Begriffe", not re.search(r"Risk Score|confidence|Anspruch|berechtigt|durchsetzbar|§", text))

    at.text_input(key="pos_suche").input("schalung").run()
    check("Suche wirkt in der App", tabelle_oz(at) == ["2.2"], str(tabelle_oz(at)))
    at.text_input(key="pos_suche").input("gibtesnicht").run()
    check("Leerer Filter: Hinweis", not at.exception and any("Keine Position" in x.value for x in at.info))
    at.text_input(key="pos_suche").input("").run()
    at.toggle(key="pos_nur_fund").set_value(True).run()
    check("„Nur mit Fund“ wirkt", tabelle_oz(at) == ["1.2", "1.10", "2.1", "2.3"], str(tabelle_oz(at)))
    at.toggle(key="pos_nur_fund").set_value(False).run()
    at.multiselect(key="pos_stufe").set_value([4]).run()
    check("Stufenfilter wirkt", tabelle_oz(at) == ["2.1"], str(tabelle_oz(at)))
    at.multiselect(key="pos_stufe").set_value([]).run()
    at.multiselect(key="pos_titel").set_value(["Erdbau"]).run()
    check("Titelfilter wirkt", tabelle_oz(at) == ["1.2", "1.10"], str(tabelle_oz(at)))
    at.multiselect(key="pos_titel").set_value([]).run()
    at.selectbox(key="pos_sortierung").set_value("Anzahl Funde").run()
    check("Sortierung wirkt", tabelle_oz(at)[0] == "2.1", str(tabelle_oz(at)))
    at.selectbox(key="pos_wahl").set_value(2).run()
    text = alle_texte(at)
    check("Detail: Kurz- und Langtext", "Stützwand C30/37" in text and "Beton C25/30" in text)
    check("Detail: Funde der Position mit Beleg", "Funde dieser Position (2)" in text and "lv-beleg" in text)
    check("Detail: Kategorie und neutrale Stufe", ":orange-badge[möglicher Widerspruch]" in text
          and ":gray-badge[1 – Fehlerprüfung]" in text)
    check("Detail: leerer EP als „–“", not at.exception)
    at.selectbox(key="pos_wahl").set_value(3).run()
    text = alle_texte(at)
    check("Position ohne Fund: keine Entwarnung", "Das heißt nicht, dass die Position ohne Fehler" in text)
    check("Fehlende Werte nie 0,00", "0,00" not in text.split("OZ 2.2")[-1])

    if len(sys.argv) > 1:
        os.environ["LV_FINDINGS_DIR"] = tempfile.mkdtemp()
        from bericht import pruefe_lv
        gesamt = fehler = 0
        for pfad in sorted(Path(sys.argv[1]).iterdir()):
            if pfad.name == ".DS_Store" or pfad.suffix.lower() == ".docx":
                continue
            funde, _, info = pruefe_lv(pfad)
            zz = P.zuordnen(info["tabelle"], funde)
            gesamt += len(funde)
            if len(zz) != info["positionen"] or P.fund_ids(zz) != {f["id"] for f in funde}:
                fehler += 1
                print("  Abweichung:", pfad.name)
        check(f"Alle Dateien: Fund-IDs je LV vollständig ({gesamt} Funde)", fehler == 0 and gesamt > 0, str(gesamt))

    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
