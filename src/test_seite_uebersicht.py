"""
test_seite_uebersicht.py - Tests für src/pages/0_Uebersicht.py (Block B8a, Sitzung B2). Nur AppTest im Prozess
(kein Port, kein Browser, schreibt nichts; Team 19:55, B2-F13) und erfundene Funde im session_state.
Aufruf aus src/ (mit --with streamlit==1.67.0 …):  python test_seite_uebersicht.py
"""
import re
import sys
import tomllib
from pathlib import Path

from streamlit.testing.v1 import AppTest

SEITE = str(Path(__file__).with_name("pages") / "0_Uebersicht.py")
ergebnisse = []


def check(name, ok, detail=""):
    ergebnisse.append(ok)
    print(f"{'OK    ' if ok else 'FEHLER'} {name}" + (f" – {detail}" if detail and not ok else ""))


def fund(nr, stufe, rang, oz, beleg, kat="Risikohinweis", titel="T"):
    return {"id": f"{nr}|demo.X83|{oz}", "pruefung": nr, "kategorie": kat, "titel": titel,
            "positionen": [{"datei": "demo.X83", "oz": oz, "seite": None}], "belege": [beleg], "feldbelege": [],
            "begruendung": "b", "stufe": stufe, "stufe_begruendung": "s", "prioritaet_in_stufe": rang,
            "rueckfrage": None, "status": "offen"}


FUNDE = [fund(6, 2, 1, "1.2", "Wasserhaltung", titel="Pauschale (psch)"),
         fund(9, 3, 1, "1.3", "Bauschutt laden und entsorgen", titel="Entsorgung, Schadstoffe"),
         fund(1, 1, 7, "1.1", "Druckrohr DN 150", kat="möglicher Widerspruch", titel="Nennweite (DN) im Kurztext ≠ Langtext"),
         fund(12, 4, 5, "1.5", "wie vor, jedoch H 2,5 m", kat="Unklarheit", titel="Verweistext"),
         fund(10, 3, 2, "1.4", "Bauzaun vorhalten", titel="Vorhalten, bauzeitabhängig"),
         fund(16, 1, 4, "1.6", "Rinnenplatte 30 cm", kat="möglicher Widerspruch", titel="Gleiche Leistung"),
         fund(9, 3, 1, "1.4", "Bauzaun entsorgen", titel="Entsorgung, Schadstoffe")]
KURZ = {"1.1": "Druckrohr PE-HD DN 150", "1.2": "Wasserhaltung", "1.3": "Bauschutt", "1.4": "Bauzaun",
        "1.5": "wie vor, jedoch", "1.6": "Rinnenplatte"}
ZUSTAND = {"lv_name": "Demo-LV.X83", "format": "GAEB XML", "positionen": 6, "nur_preise": False,
           "abdeckung": [{"pruefung": 1, "name": "Nennweite", "pruefbar": 4, "gesamt": 6,
                          "gruende": [("ohne eigenen Langtext", 2)]}],
           "funde": FUNDE, "kurztexte": KURZ, "gp": {o: None for o in KURZ}, "ki_aktiv": False}


def lauf(zustand, downloads=None):
    at = AppTest.from_file(SEITE)
    if zustand is not None:
        at.session_state["lv_uebersicht"] = zustand
    if downloads is not None:
        at.session_state["lv_downloads"] = downloads
    return at.run(timeout=60)


def texte(at):
    t = [m.value for m in at.markdown] + [c.value for c in at.caption] + [x.value for x in at.info] + \
        [x.value for x in at.warning] + [x.value for x in at.text] + [m.label for m in at.metric] + \
        [h.value for h in at.subheader] + [h.value for h in at.title]
    return [str(x) for x in t]


if __name__ == "__main__":
    at = lauf(None)
    check("ohne Ergebnis: Hinweis statt Ausnahme", not at.exception and any("Noch kein LV geprüft" in x for x in texte(at)))

    at = lauf(ZUSTAND)
    check("unbepreist: keine Ausnahme", not at.exception, str(at.exception))
    m = {x.label: int(x.value) for x in at.metric}
    check("Kacheln je Stufe mit Namen, alle 4 auch bei 0", list(m) == ["1 – Fehlerprüfung", "2 – Kalkulationsrisiko",
                                                                       "3 – mögliches Nachtragspotenzial", "4 – Unklarheit"])
    check("Kachel-Summen = Fundzahl", sum(m.values()) == len(FUNDE) and m["3 – mögliches Nachtragspotenzial"] == 3, str(m))
    t = texte(at)
    check("„Positionswert“ nur bei bepreisten LVs (hier nicht)", not any("Positionswert" in x for x in t))
    belege = [x for x in t if x.startswith("> ")]
    check("„Zuerst ansehen“: 5 Funde in Sortierung Stufe, Rang, OZ mit wörtlichem Beleg",
          belege == ["> Rinnenplatte 30 cm", "> Druckrohr DN 150", "> Wasserhaltung", "> Bauschutt laden und entsorgen",
                     "> Bauzaun entsorgen"], str(belege))
    check("Prüfabdeckung im Kopf", any("prüfbar in 4 von 6 Positionen" in x for x in t))
    check("KI-Hinweis nach E13", any("KI-Vorschläge entwarnen nie" in x for x in t))
    check("kein Dateipfad im Text", not any(re.search(r"data/|/Users|\\\\|[A-Z]:\\\\", x) for x in t))
    check("Diagramm vorhanden", len(at.get("vega_lite_chart")) == 1)

    bepreist = dict(ZUSTAND, gp={"1.1": 1500.0, "1.2": 2000.0, "1.3": 300.0, "1.4": 50.5, "1.5": 10.0, "1.6": 0.0})
    at = lauf(bepreist, downloads=[{"label": "Risikobericht (.xlsx)", "daten": b"x", "dateiname": "r.xlsx",
                                    "mime": "application/octet-stream"}])
    t = texte(at)
    pw = [x for x in t if x.startswith("Positionswert laut LV (Summe GP) – kein Risikobetrag")]
    # Stufe 1: 1.1 + 1.6 = 1.500,00; Stufe 2: 1.2 = 2.000,00; Stufe 3: 1.3 + 1.4 (einmal) = 350,50; Stufe 4: 1.5 = 10,00
    check("bepreist: Positionswert je Stufe, Position je Stufe einmal gezählt",
          pw == ["Positionswert laut LV (Summe GP) – kein Risikobetrag: 1.500,00 €",
                 "Positionswert laut LV (Summe GP) – kein Risikobetrag: 2.000,00 €",
                 "Positionswert laut LV (Summe GP) – kein Risikobetrag: 350,50 €",
                 "Positionswert laut LV (Summe GP) – kein Risikobetrag: 10,00 €"], str(pw))
    check("bepreist: keine Ausnahme, Download-Knopf aus session_state", not at.exception
          and len(at.get("download_button")) == 1)
    at = lauf(dict(ZUSTAND, funde=[], nur_preise=True, positionen=249))
    check("nur Preise, keine Funde: Hinweis, Kacheln 0, keine Ausnahme",
          not at.exception and sum(int(x.value) for x in at.metric) == 0 and any("nur Preise" in x for x in texte(at)))

    cfg = tomllib.loads((Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    check("Farbschema: Dark und Light im Theme, Stufen ohne Warnfarbe (R6)",
          {"dark", "light"} <= set(cfg["theme"]) and "FARBEN" not in Path(SEITE).read_text(encoding="utf-8"))
    print(f"\n{sum(ergebnisse)}/{len(ergebnisse)} Tests bestanden")
    sys.exit(0 if all(ergebnisse) else 1)
